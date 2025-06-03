import json
from typing import Dict, Any
from datetime import datetime

class GPXConverter:
    """Convert processed GPX data to database-ready JSONB format"""
    
    def __init__(self):
        pass
    
    def convert_to_jsonb(self, processed_data: Dict) -> Dict[str, Any]:
        """
        Convert processed GPX data to JSONB format for database storage
        
        Args:
            processed_data: Output from GPXProcessor.parse_gpx_file()
            
        Returns:
            Dictionary ready for JSONB storage and extracted fields
        """
        try:
            # Prepare JSONB data structure
            jsonb_data = {
                'track_info': {
                    'waypoint_count': processed_data['statistics'].get('waypoint_count', 0),
                    'creator': processed_data['metadata'].get('creator', 'Unknown'),
                    'version': processed_data['metadata'].get('version', '1.1')
                },
                'waypoints': processed_data['waypoints'],
                'statistics': processed_data['statistics']
            }
            
            # Extract key fields for database columns
            extracted_fields = self._extract_key_fields(processed_data['statistics'])
            
            return {
                'jsonb_track_data': jsonb_data,
                'extracted_fields': extracted_fields
            }
            
        except Exception as e:
            raise Exception(f"Error converting GPX data to JSONB: {str(e)}")
    
    def _extract_key_fields(self, statistics: Dict) -> Dict[str, Any]:
        """
        Extract key fields for database columns from statistics
        
        Args:
            statistics: Statistics from processed GPX data
            
        Returns:
            Dictionary with extracted fields for database columns
        """
        extracted = {}
        
        # Time fields
        if 'start_time' in statistics:
            extracted['start_time'] = self._parse_datetime(statistics['start_time'])
        
        if 'end_time' in statistics:
            extracted['end_time'] = self._parse_datetime(statistics['end_time'])
        
        # Distance field
        if 'total_distance_km' in statistics:
            extracted['total_distance'] = statistics['total_distance_km']
        
        # Duration field
        if 'total_duration_seconds' in statistics:
            # Convert seconds to PostgreSQL INTERVAL format
            duration_seconds = statistics['total_duration_seconds']
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            seconds = duration_seconds % 60
            extracted['total_duration'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Speed fields
        if 'max_speed_kmh' in statistics:
            extracted['max_speed'] = statistics['max_speed_kmh']
        
        if 'avg_speed_kmh' in statistics:
            extracted['avg_speed'] = statistics['avg_speed_kmh']
        
        return extracted
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """
        Parse ISO datetime string to datetime object
        
        Args:
            datetime_str: ISO format datetime string
            
        Returns:
            datetime object
        """
        try:
            # Handle both with and without timezone info
            if datetime_str.endswith('+00:00'):
                return datetime.fromisoformat(datetime_str)
            elif datetime_str.endswith('Z'):
                return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(datetime_str)
        except Exception as e:
            raise ValueError(f"Invalid datetime format: {datetime_str}")
    
    def validate_jsonb_data(self, jsonb_data: Dict) -> bool:
        """
        Validate JSONB data structure
        
        Args:
            jsonb_data: JSONB data to validate
            
        Returns:
            True if valid, raises exception if invalid
        """
        required_keys = ['track_info', 'waypoints', 'statistics']
        
        for key in required_keys:
            if key not in jsonb_data:
                raise ValueError(f"Missing required key in JSONB data: {key}")
        
        # Validate waypoints structure
        if not isinstance(jsonb_data['waypoints'], list):
            raise ValueError("Waypoints must be a list")
        
        if len(jsonb_data['waypoints']) == 0:
            raise ValueError("Waypoints list cannot be empty")
        
        # Validate each waypoint has required fields
        required_waypoint_fields = ['latitude', 'longitude']
        for i, waypoint in enumerate(jsonb_data['waypoints']):
            for field in required_waypoint_fields:
                if field not in waypoint:
                    raise ValueError(f"Waypoint {i} missing required field: {field}")
        
        return True