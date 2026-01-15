"""API client for mobile app to communicate with backend."""

import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


class APIClient:
    """Client for communicating with AR Golf Tracker backend API."""
    
    def __init__(self, base_url: str, access_token: Optional[str] = None):
        """Initialize API client.
        
        Args:
            base_url: Base URL of the backend API (e.g., "https://api.argolftracker.com")
            access_token: JWT access token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.session = requests.Session()
        
        if access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {access_token}'
            })
    
    def set_access_token(self, token: str) -> None:
        """Set or update the access token.
        
        Args:
            token: JWT access token
        """
        self.access_token = token
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
    
    def login(self, email: str, password: str) -> Dict[str, str]:
        """Authenticate user and get tokens.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Dictionary with access_token and refresh_token
            
        Raises:
            requests.HTTPError: If authentication fails
        """
        response = self.session.post(
            f'{self.base_url}/api/v1/auth/login',
            json={'email': email, 'password': password}
        )
        response.raise_for_status()
        
        data = response.json()
        self.set_access_token(data['access_token'])
        return data
    
    def get_rounds(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get list of rounds for authenticated user.
        
        Args:
            limit: Maximum number of rounds to return
            offset: Number of rounds to skip
            
        Returns:
            List of round dictionaries with date, course, and metadata
            
        Raises:
            requests.HTTPError: If request fails
        """
        response = self.session.get(
            f'{self.base_url}/api/v1/rounds',
            params={'limit': limit, 'offset': offset}
        )
        response.raise_for_status()
        return response.json()
    
    def get_round(self, round_id: str) -> Dict[str, Any]:
        """Get details of a specific round.
        
        Args:
            round_id: Round ID
            
        Returns:
            Round details dictionary
            
        Raises:
            requests.HTTPError: If round not found or request fails
        """
        response = self.session.get(
            f'{self.base_url}/api/v1/rounds/{round_id}'
        )
        response.raise_for_status()
        return response.json()
    
    def get_round_shots(self, round_id: str) -> List[Dict[str, Any]]:
        """Get all shots for a specific round.
        
        Args:
            round_id: Round ID
            
        Returns:
            List of shot dictionaries
            
        Raises:
            requests.HTTPError: If round not found or request fails
        """
        response = self.session.get(
            f'{self.base_url}/api/v1/rounds/{round_id}/shots'
        )
        response.raise_for_status()
        return response.json()
    
    def get_course(self, course_id: str) -> Dict[str, Any]:
        """Get details of a specific course.
        
        Args:
            course_id: Course ID
            
        Returns:
            Course details dictionary
            
        Raises:
            requests.HTTPError: If course not found or request fails
        """
        response = self.session.get(
            f'{self.base_url}/api/v1/courses/{course_id}'
        )
        response.raise_for_status()
        return response.json()
    
    def get_course_holes(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all holes for a specific course.
        
        Args:
            course_id: Course ID
            
        Returns:
            List of hole dictionaries
            
        Raises:
            requests.HTTPError: If course not found or request fails
        """
        response = self.session.get(
            f'{self.base_url}/api/v1/courses/{course_id}/holes'
        )
        response.raise_for_status()
        return response.json()
    
    def search_courses(self, lat: float, lon: float, radius: int = 1000) -> List[Dict[str, Any]]:
        """Search for courses near a GPS location.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius: Search radius in meters (default 1000)
            
        Returns:
            List of nearby courses with distances
            
        Raises:
            requests.HTTPError: If request fails
        """
        response = self.session.get(
            f'{self.base_url}/api/v1/courses/search',
            params={'lat': lat, 'lon': lon, 'radius': radius}
        )
        response.raise_for_status()
        return response.json()
