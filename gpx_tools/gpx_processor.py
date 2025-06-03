import gpxpy
import pytz
from datetime import datetime
from typing import List, Dict, Optional
import math


class GPXProcessor:
    def __init__(self, timezone: str = 'America/Toronto'):
        """
        Initialize GPX processor with timezone for time conversion
        
        Args:
            timezone: Target timezone for conversion (default: America/Toronto)
        """
        self.timezone = pytz.timezone(timezone)
    
    def parse_gpx_file(self, file_path: str, skip_points: int = 0) -> Dict:
        """
        Parse GPX file from file path and extract track data with timezone conversion
        
        Args:
            file_path: Path to GPX file
            skip_points: Number of points to skip for speed calculation (default: 1)
            
        Returns:
            Dictionary containing waypoints and metadata
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                gpx_content = file.read()
            return self.parse_gpx(gpx_content, skip_points)
            
        except Exception as e:
            raise Exception(f"Error reading GPX file {file_path}: {str(e)}")
    
    def parse_gpx(self, gpx_content: str, skip_points: int = 0) -> Dict:
        """
        Parse GPX content string and extract track data with timezone conversion
        
        Args:
            gpx_content: Raw GPX file content as string
            skip_points: Number of points to skip for speed calculation (default: 1)
            
        Returns:
            Dictionary containing waypoints and metadata
        """
        try:
            # Parse GPX using gpxpy
            gpx = gpxpy.parse(gpx_content)
            waypoints = []
            
            # Extract waypoints from all tracks and segments
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        # Convert UTC time to local timezone
                        local_time = None
                        if point.time:
                            local_time = point.time.astimezone(self.timezone)
                        
                        waypoint = {
                            'latitude': point.latitude,
                            'longitude': point.longitude,
                            'timestamp': local_time.strftime('%Y-%m-%dT%H:%M:%S') if local_time else None,
                            'elevation': point.elevation or 0.0
                        }
                        waypoints.append(waypoint)
            
            if not waypoints:
                raise ValueError("No valid waypoints found in GPX file")
            
            # Calculate track statistics
            statistics = self._calculate_track_statistics(waypoints, skip_points)
            
            # Get metadata from GPX
            track_info = {
                'creator': getattr(gpx, 'creator', 'Unknown'),
                'version': getattr(gpx, 'version', '1.1'),
                'name': getattr(gpx, 'name', None),
                'description': getattr(gpx, 'description', None),
                'waypoint_count': len(waypoints),
                'track_count': len(gpx.tracks),
                'route_count': len(gpx.routes) if hasattr(gpx, 'routes') else 0,
                'waypoint_count_gpx': len(gpx.waypoints) if hasattr(gpx, 'waypoints') else 0
            }
            
            return {
                'waypoints': waypoints,
                'statistics': statistics,
                'metadata': track_info
            }
            
        except Exception as e:
            raise Exception(f"Error parsing GPX file: {str(e)}")
    
    def _calculate_track_statistics(self, waypoints: List[Dict], skip_points: int = 0) -> Dict:
        """
        Calculate comprehensive track statistics
        
        Args:
            waypoints: List of waypoint dictionaries
            skip_points: Number of points to skip for speed calculation (0 = use all points)
            
        Returns:
            Dictionary containing track statistics
        """
        if len(waypoints) < 2:
            return {}
        
        # Calculate total distance
        total_distance = 0.0
        for i in range(1, len(waypoints)):
            distance = self._calculate_distance(
                waypoints[i-1]['latitude'], waypoints[i-1]['longitude'],
                waypoints[i]['latitude'], waypoints[i]['longitude']
            )
            total_distance += distance
        
        # Calculate speeds with skip interval
        speeds = self._calculate_speeds_with_skip(waypoints, skip_points)
        
        # Time calculations - use the already converted local timestamps
        start_time_str = waypoints[0]['timestamp']
        end_time_str = waypoints[-1]['timestamp']
        
        # Handle ISO format: "2025-05-21T19:12:14"
        start_time_naive = datetime.fromisoformat(start_time_str)
        end_time_naive = datetime.fromisoformat(end_time_str)
        
        # Time calculations
        start_time = self.timezone.localize(start_time_naive)
        end_time = self.timezone.localize(end_time_naive)
        total_duration = (end_time - start_time).total_seconds()
        print(f"DEBUG: Original timestamps: {start_time_str} -> {end_time_str}")
        print(f"DEBUG: Localized times: {start_time} -> {end_time}")
        print(f"DEBUG: Localized times: {start_time.strftime('%Y-%m-%d %H:%M:%S')} -> {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Basic statistics
        stats = {
            'total_distance_km': round(total_distance, 2),
            'total_duration_seconds': int(total_duration),
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'waypoint_count': len(waypoints),
            'speed_samples': len(speeds),
            'raw_speeds': speeds
        }
        
        # Speed statistics (if we have valid speed data)
        if speeds:
            filtered_speeds = self._filter_by_outliers(speeds)
            #filtered_speeds = speeds
            
            if filtered_speeds:
                stats.update({
                    'max_speed_kmh': round(max(filtered_speeds), 2),
                    'avg_speed_kmh': round(sum(filtered_speeds) / len(filtered_speeds), 2),
                    'speed_outliers_filtered': len(speeds) - len(filtered_speeds)
                })
        
        return stats
    
    def _calculate_speeds_with_skip(self, waypoints: List[Dict], skip_points: int = 0) -> List[float]:
        """
        Calculate speeds with point skipping for noise reduction
        
        Args:
            waypoints: List of waypoint dictionaries
            skip_points: Number of points to skip between calculations
            
        Returns:
            List of speeds in km/h
        """
        speeds = []
        interval = skip_points + 1  # Convert skip_points to interval
        
        for i in range(interval, len(waypoints)):
            try:
                # Get points with interval
                point1 = waypoints[i - interval]
                point2 = waypoints[i]
                
                # Calculate distance
                distance = self._calculate_distance(
                    point1['latitude'], point1['longitude'],
                    point2['latitude'], point2['longitude']
                )
                
                # Calculate time difference
                time1 = datetime.fromisoformat(point1['timestamp'])
                time2 = datetime.fromisoformat(point2['timestamp'])
                time_diff = (time2 - time1).total_seconds()
                
                if time_diff > 0:
                    # Speed in km/h
                    speed = (distance / time_diff) * 3.6
                    speeds.append(speed)
                    
            except (ValueError, TypeError, KeyError) as e:
                # Skip invalid data points
                continue
        
        return speeds
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two geographic points using Haversine formula
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in meters
        """
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in meters
        earth_radius = 6371000
        return earth_radius * c
    
    def _filter_by_outliers(self, speeds: List[float], max_speed: float = 200.0) -> List[float]:
        """
        Filter out unrealistic speed values
        
        Args:
            speeds: List of speed values in km/h
            max_speed: Maximum realistic speed in km/h
            
        Returns:
            Filtered list of speeds
        """
        return [speed for speed in speeds if 0 <= speed <= max_speed]