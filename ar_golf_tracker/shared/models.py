"""Core data models for AR Golf Tracker system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from datetime import datetime


class ClubType(Enum):
    """Golf club types."""
    DRIVER = "DRIVER"
    WOOD_3 = "WOOD_3"
    WOOD_5 = "WOOD_5"
    HYBRID_3 = "HYBRID_3"
    HYBRID_4 = "HYBRID_4"
    HYBRID_5 = "HYBRID_5"
    IRON_3 = "IRON_3"
    IRON_4 = "IRON_4"
    IRON_5 = "IRON_5"
    IRON_6 = "IRON_6"
    IRON_7 = "IRON_7"
    IRON_8 = "IRON_8"
    IRON_9 = "IRON_9"
    PITCHING_WEDGE = "PITCHING_WEDGE"
    SAND_WEDGE = "SAND_WEDGE"
    LOB_WEDGE = "LOB_WEDGE"
    PUTTER = "PUTTER"


class DistanceUnit(Enum):
    """Distance measurement units."""
    YARDS = "YARDS"
    METERS = "METERS"


class DistanceAccuracy(Enum):
    """GPS-based distance calculation accuracy levels."""
    HIGH = "HIGH"      # Both GPS positions < 10m accuracy
    MEDIUM = "MEDIUM"  # Either GPS position 10-20m accuracy
    LOW = "LOW"        # Either GPS position > 20m accuracy


class SyncStatus(Enum):
    """Data synchronization status."""
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


@dataclass
class GPSPosition:
    """GPS coordinates with accuracy information."""
    latitude: float
    longitude: float
    accuracy: float  # meters
    timestamp: int   # Unix timestamp
    altitude: Optional[float] = None


@dataclass
class Distance:
    """Shot distance with accuracy information."""
    value: float
    unit: DistanceUnit
    accuracy: DistanceAccuracy


@dataclass
class Shot:
    """Individual golf shot record."""
    id: str
    round_id: str
    hole_number: int
    swing_number: int
    club_type: ClubType
    timestamp: int  # Unix timestamp
    gps_origin: GPSPosition
    distance: Optional[Distance] = None
    notes: Optional[str] = None
    sync_status: SyncStatus = SyncStatus.PENDING


@dataclass
class WeatherConditions:
    """Weather conditions during a round."""
    temperature: Optional[float] = None  # Celsius
    wind_speed: Optional[float] = None   # km/h
    wind_direction: Optional[str] = None
    conditions: Optional[str] = None     # "sunny", "cloudy", "rainy", etc.


@dataclass
class Round:
    """Golf round containing multiple shots."""
    id: str
    user_id: str
    course_id: str
    course_name: str
    start_time: int  # Unix timestamp
    end_time: Optional[int] = None
    shots: List[Shot] = field(default_factory=list)
    weather: Optional[WeatherConditions] = None
    sync_status: SyncStatus = SyncStatus.PENDING


@dataclass
class GeoPolygon:
    """Geographic polygon for course features."""
    coordinates: List[tuple[float, float]]  # [(longitude, latitude), ...]


@dataclass
class Hazard:
    """Golf course hazard."""
    type: str  # "WATER", "BUNKER", "TREES", "OUT_OF_BOUNDS"
    polygon: GeoPolygon


@dataclass
class Hole:
    """Golf course hole information."""
    id: str
    course_id: str
    hole_number: int
    par: int
    yardage: int
    tee_box_location: GPSPosition
    green_location: GPSPosition
    fairway_polygon: Optional[GeoPolygon] = None
    hazards: List[Hazard] = field(default_factory=list)


@dataclass
class Course:
    """Golf course information."""
    id: str
    name: str
    location: GPSPosition  # Course center point
    address: str
    total_holes: int
    par: int
    yardage: int
    holes: List[Hole] = field(default_factory=list)


@dataclass
class UserPreferences:
    """User preferences and settings."""
    distance_unit: DistanceUnit = DistanceUnit.YARDS
    auto_sync: bool = True
    data_retention_days: int = 730  # 2 years default


@dataclass
class SwingProfile:
    """User swing characteristics for calibration."""
    average_swing_speed: float  # mph
    swing_tempo: float
    dominant_hand: str  # "LEFT" or "RIGHT"


@dataclass
class UserProfile:
    """User account and profile information."""
    id: str
    email: str
    preferences: UserPreferences = field(default_factory=UserPreferences)
    calibration_model_key: Optional[str] = None  # S3 key for custom club recognition model
    swing_profile: Optional[SwingProfile] = None
