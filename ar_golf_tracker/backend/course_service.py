"""Course identification and management service."""

from typing import Optional, List, Tuple
from ar_golf_tracker.shared.models import Course, Hole, GPSPosition, GeoPolygon, Hazard
from ar_golf_tracker.backend.database import CloudDatabase
import json


class CourseService:
    """Service for identifying courses and loading course data."""
    
    def __init__(self, db: CloudDatabase):
        """Initialize course service.
        
        Args:
            db: CloudDatabase instance
        """
        self.db = db
    
    def find_courses_by_location(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 1000
    ) -> List[Tuple[str, str, float]]:
        """Find golf courses near a GPS location.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_meters: Search radius in meters (default 1000m)
        
        Returns:
            List of tuples (course_id, course_name, distance_meters)
        """
        conn = self.db.connect()
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM find_courses_near_location(%s, %s, %s)
            """, (latitude, longitude, radius_meters))
            
            results = cursor.fetchall()
            return [(str(row[0]), row[1], row[2]) for row in results]
    
    def identify_course(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 1000
    ) -> Optional[str]:
        """Identify the golf course at a GPS location.
        
        Returns the closest course within the search radius.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_meters: Search radius in meters (default 1000m)
        
        Returns:
            Course ID if found, None otherwise
        """
        courses = self.find_courses_by_location(latitude, longitude, radius_meters)
        
        if courses:
            # Return the closest course
            return courses[0][0]
        
        return None
    
    def load_course(self, course_id: str) -> Optional[Course]:
        """Load complete course data including holes.
        
        Args:
            course_id: UUID of the course
        
        Returns:
            Course object with all holes, or None if not found
        """
        conn = self.db.connect()
        
        with conn.cursor() as cursor:
            # Load course data
            cursor.execute("""
                SELECT 
                    id, name, 
                    ST_Y(location::geometry) as latitude,
                    ST_X(location::geometry) as longitude,
                    address, total_holes, par, yardage
                FROM courses
                WHERE id = %s
            """, (course_id,))
            
            course_row = cursor.fetchone()
            if not course_row:
                return None
            
            # Load holes for this course
            cursor.execute("""
                SELECT 
                    id, course_id, hole_number, par, yardage,
                    ST_Y(tee_box_location::geometry) as tee_lat,
                    ST_X(tee_box_location::geometry) as tee_lon,
                    ST_Y(green_location::geometry) as green_lat,
                    ST_X(green_location::geometry) as green_lon,
                    ST_AsGeoJSON(fairway_polygon) as fairway_geojson,
                    hazards
                FROM holes
                WHERE course_id = %s
                ORDER BY hole_number
            """, (course_id,))
            
            holes = []
            for hole_row in cursor.fetchall():
                # Parse fairway polygon if present
                fairway_polygon = None
                if hole_row[9]:  # fairway_geojson
                    fairway_data = json.loads(hole_row[9])
                    if fairway_data and 'coordinates' in fairway_data:
                        # GeoJSON polygon coordinates are [[[lon, lat], ...]]
                        coords = fairway_data['coordinates'][0]
                        fairway_polygon = GeoPolygon(coordinates=[(c[0], c[1]) for c in coords])
                
                # Parse hazards if present
                hazards = []
                if hole_row[10]:  # hazards JSONB
                    hazards_data = hole_row[10]
                    for hazard_dict in hazards_data:
                        hazard_polygon = GeoPolygon(
                            coordinates=[(c[0], c[1]) for c in hazard_dict['polygon']['coordinates']]
                        )
                        hazards.append(Hazard(
                            type=hazard_dict['type'],
                            polygon=hazard_polygon
                        ))
                
                hole = Hole(
                    id=str(hole_row[0]),
                    course_id=str(hole_row[1]),
                    hole_number=hole_row[2],
                    par=hole_row[3],
                    yardage=hole_row[4],
                    tee_box_location=GPSPosition(
                        latitude=hole_row[5],
                        longitude=hole_row[6],
                        accuracy=5.0,  # Assume high accuracy for course data
                        timestamp=0
                    ),
                    green_location=GPSPosition(
                        latitude=hole_row[7],
                        longitude=hole_row[8],
                        accuracy=5.0,
                        timestamp=0
                    ),
                    fairway_polygon=fairway_polygon,
                    hazards=hazards
                )
                holes.append(hole)
            
            # Create course object
            course = Course(
                id=str(course_row[0]),
                name=course_row[1],
                location=GPSPosition(
                    latitude=course_row[2],
                    longitude=course_row[3],
                    accuracy=5.0,
                    timestamp=0
                ),
                address=course_row[4],
                total_holes=course_row[5],
                par=course_row[6],
                yardage=course_row[7],
                holes=holes
            )
            
            return course
    
    def get_course_layout(self, course_id: str) -> Optional[dict]:
        """Get course layout information (holes, distances, boundaries).
        
        Args:
            course_id: UUID of the course
        
        Returns:
            Dictionary with course layout data, or None if not found
        """
        course = self.load_course(course_id)
        
        if not course:
            return None
        
        return {
            "course_id": course.id,
            "course_name": course.name,
            "total_holes": course.total_holes,
            "par": course.par,
            "yardage": course.yardage,
            "holes": [
                {
                    "hole_number": hole.hole_number,
                    "par": hole.par,
                    "yardage": hole.yardage,
                    "tee_box": {
                        "latitude": hole.tee_box_location.latitude,
                        "longitude": hole.tee_box_location.longitude
                    },
                    "green": {
                        "latitude": hole.green_location.latitude,
                        "longitude": hole.green_location.longitude
                    },
                    "has_fairway_data": hole.fairway_polygon is not None,
                    "hazard_count": len(hole.hazards)
                }
                for hole in course.holes
            ]
        }
