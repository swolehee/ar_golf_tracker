"""Distance calculation service using Haversine formula for GPS-based shot distances."""

import math
from typing import Optional
from ar_golf_tracker.shared.models import (
    GPSPosition, Distance, DistanceUnit, DistanceAccuracy
)


class DistanceCalculationService:
    """Calculates shot distances from GPS positions using Haversine formula."""
    
    # Earth's radius in meters
    EARTH_RADIUS_METERS = 6371000.0
    
    # GPS accuracy thresholds for distance accuracy classification
    HIGH_ACCURACY_THRESHOLD = 10.0   # meters
    MEDIUM_ACCURACY_THRESHOLD = 20.0  # meters
    
    def __init__(self, default_unit: DistanceUnit = DistanceUnit.YARDS):
        """Initialize distance calculation service.
        
        Args:
            default_unit: Default unit for distance calculations (YARDS or METERS)
        """
        self.default_unit = default_unit
    
    def calculate_distance(
        self,
        from_position: GPSPosition,
        to_position: GPSPosition,
        unit: Optional[DistanceUnit] = None
    ) -> Distance:
        """Calculate distance between two GPS positions using Haversine formula.
        
        The Haversine formula accounts for Earth's curvature and provides accurate
        distances for positions on a sphere. When altitude data is available,
        elevation changes are included in the calculation.
        
        Args:
            from_position: Starting GPS position
            to_position: Ending GPS position
            unit: Distance unit (defaults to service default_unit)
            
        Returns:
            Distance object with value, unit, and accuracy classification
        """
        if unit is None:
            unit = self.default_unit
        
        # Calculate horizontal distance using Haversine formula
        horizontal_distance = self._haversine_distance(from_position, to_position)
        
        # Add elevation adjustment if altitude data available
        total_distance = horizontal_distance
        if from_position.altitude is not None and to_position.altitude is not None:
            elevation_change = abs(to_position.altitude - from_position.altitude)
            # Use Pythagorean theorem: total = sqrt(horizontal^2 + vertical^2)
            total_distance = math.sqrt(horizontal_distance**2 + elevation_change**2)
        
        # Classify accuracy based on GPS accuracy of both positions
        accuracy = self._classify_accuracy(from_position, to_position)
        
        # Convert to requested unit
        distance_value = self._convert_distance(total_distance, unit)
        
        return Distance(
            value=distance_value,
            unit=unit,
            accuracy=accuracy
        )
    
    def _haversine_distance(
        self,
        pos1: GPSPosition,
        pos2: GPSPosition
    ) -> float:
        """Calculate great-circle distance using Haversine formula.
        
        The Haversine formula:
        a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
        c = 2 * atan2(√a, √(1−a))
        d = R * c
        
        where:
        - Δlat is the difference in latitude
        - Δlon is the difference in longitude
        - R is Earth's radius
        
        Args:
            pos1: First GPS position
            pos2: Second GPS position
            
        Returns:
            Distance in meters
        """
        # Convert latitude and longitude to radians
        lat1_rad = math.radians(pos1.latitude)
        lat2_rad = math.radians(pos2.latitude)
        delta_lat = math.radians(pos2.latitude - pos1.latitude)
        delta_lon = math.radians(pos2.longitude - pos1.longitude)
        
        # Haversine formula
        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # Distance in meters
        distance_meters = self.EARTH_RADIUS_METERS * c
        
        return distance_meters
    
    def _classify_accuracy(
        self,
        pos1: GPSPosition,
        pos2: GPSPosition
    ) -> DistanceAccuracy:
        """Classify distance accuracy based on GPS position accuracies.
        
        Classification rules:
        - HIGH: Both positions have accuracy < 10 meters
        - MEDIUM: Either position has accuracy 10-20 meters
        - LOW: Either position has accuracy > 20 meters
        
        Args:
            pos1: First GPS position
            pos2: Second GPS position
            
        Returns:
            Distance accuracy classification
        """
        max_accuracy = max(pos1.accuracy, pos2.accuracy)
        
        if max_accuracy > self.MEDIUM_ACCURACY_THRESHOLD:
            return DistanceAccuracy.LOW
        elif max_accuracy > self.HIGH_ACCURACY_THRESHOLD:
            return DistanceAccuracy.MEDIUM
        else:
            return DistanceAccuracy.HIGH
    
    def _convert_distance(self, distance_meters: float, unit: DistanceUnit) -> float:
        """Convert distance from meters to requested unit.
        
        Args:
            distance_meters: Distance in meters
            unit: Target unit (YARDS or METERS)
            
        Returns:
            Distance in requested unit, rounded to 1 decimal place
        """
        if unit == DistanceUnit.METERS:
            return round(distance_meters, 1)
        elif unit == DistanceUnit.YARDS:
            # 1 meter = 1.09361 yards
            distance_yards = distance_meters * 1.09361
            return round(distance_yards, 1)
        else:
            raise ValueError(f"Unsupported distance unit: {unit}")
