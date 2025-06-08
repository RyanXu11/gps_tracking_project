import gpxpy
import pytz
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import math

from settings.constants import TIMEZONE_STR
from .utils import (
    haversine_distance, 
    format_duration,
    detect_outliers_iqr,
    interpolate_outliers,
    safe_division
)

class GPXProcessor:
    def __init__(self, timezone: str = TIMEZONE_STR):
        """
        Initialize GPX processor with timezone
        
        Args:
            timezone: Target timezone for conversion (default: America/Toronto)
        """
        self.timezone = pytz.timezone(timezone)
    
    def parse_gpx(self, gpx_content: str) -> Dict:
        """
        Parse GPX content string and extract track data with timezone conversion
        
        Args:
            gpx_content: Raw GPX file content as string
            
        Returns:
            Dictionary containing three separate JSONB components:
            - jsonb_waypoints: Array of waypoint objects
            - jsonb_metadata: GPX file metadata object  
            - jsonb_statistics: Basic statistics object (will be enhanced by processing)
        """
        try:
            # Parse GPX using gpxpy
            gpx = gpxpy.parse(gpx_content)
            waypoints = []
            
            # Extract waypoints from all tracks and segments
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:                        
                        waypoint = {
                            'lat': point.latitude,
                            'lon': point.longitude,
                            'timestamp': point.time.isoformat() if point.time else None,
                            'elevation': point.elevation or 0.0
                        }
                        waypoints.append(waypoint)
            
            if not waypoints:
                raise ValueError("No valid waypoints found in GPX file")
            
            # Generate metadata from GPX
            jsonb_metadata = self._generate_metadata(gpx, waypoints)
            
            # Generate initial statistics structure (raw data only)
            jsonb_statistics = self._generate_basic_statistics(waypoints)
            
            return {
                'jsonb_waypoints': waypoints,
                'jsonb_metadata': jsonb_metadata,   
                'jsonb_statistics': jsonb_statistics
            }
            
        except Exception as e:
            raise Exception(f"Error parsing GPX file: {str(e)}")

    def _generate_metadata(self, gpx, waypoints: List[Dict]) -> Dict:
        """Extract metadata from GPX object"""
        metadata = {
            'waypoint_count': len(waypoints),
            'creator': getattr(gpx, 'creator', 'Unknown'),
            'version': getattr(gpx, 'version', '1.1'),
            'name': None,
            'description': None,
            'track_count': len(gpx.tracks),
            'route_count': len(gpx.routes)
        }
        
        # Try to get name and description from first track
        if gpx.tracks:
            first_track = gpx.tracks[0]
            metadata['name'] = getattr(first_track, 'name', None)
            metadata['description'] = getattr(first_track, 'description', None)
        
        return metadata
    
    def process_with_methods(self, waypoints: List[Dict], use_iqr: bool = False, 
                           window_size: int = 2,
                           interpolation_method: str = "linear") -> Dict:
        """
        Process waypoints with selected methods using pandas for efficiency
        
        Args:
            waypoints: List of waypoint dictionaries
            use_iqr: Whether to apply IQR outlier removal
            window_size: Window size for speed calculation (2=adjacent points, >2=moving average)
            interpolation_method: Pandas interpolation method ('linear', 'quadratic', 'nearest', etc.)
            
        Returns:
            Complete jsonb_statistics structure with processing results
        """
        if len(waypoints) < 2:
            return self._generate_basic_statistics(waypoints)
        
        # Start with basic metrics
        stats = self._generate_basic_statistics(waypoints)
        
        # Convert to pandas DataFrame for efficient processing
        df = pd.DataFrame(waypoints)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate initial speeds based on window size
        raw_speeds = self._calculate_speeds_with_window(df, window_size)
        
        # For comparison, always calculate adjacent speeds as baseline (window_size=2)
        baseline_speeds = self._calculate_speeds_with_window(df, 2)
        
        outliers_detected = 0
        outliers_interpolated = 0
        processed_speeds = raw_speeds.copy()
        
        # Step 1: IQR outlier detection and interpolation on speeds
        if use_iqr and len(raw_speeds) > 0:
            processed_speeds, outliers_detected, outliers_interpolated = self._detect_and_interpolate_speed_outliers(
                raw_speeds, interpolation_method
            )
        
        # Update statistics
        stats['processing_methods'] = {
            'IQR_Outlier': use_iqr,
            'Moving_Average': window_size > 2,
            'Window_Size': window_size,
            'Interpolation_Method': interpolation_method if use_iqr else None
        }
        
        stats['results'] = {
            'raw_max_speed': round(baseline_speeds.max(), 2) if len(baseline_speeds) > 0 else 0.0,
            'processed_max_speed': round(processed_speeds.max(), 2) if len(processed_speeds) > 0 else 0.0,
            'outliers_detected': int(outliers_detected),
            'outliers_interpolated': int(outliers_interpolated),
            'data_points_remaining': len(processed_speeds)
        }
        
        return stats
    
    def _detect_and_interpolate_speed_outliers(self, speeds: pd.Series, interpolation_method: str, 
                                              iqr_multiplier: float = 1.5) -> tuple:
        """
        Detect outliers in speed data using IQR method and interpolate them
        
        Args:
            speeds: Series of speed values in km/h
            interpolation_method: Pandas interpolation method ('linear', 'quadratic', etc.)
            iqr_multiplier: IQR multiplier for outlier detection (default: 1.5)
            
        Returns:
            Tuple of (processed_speeds, outliers_detected, outliers_interpolated)
        """
        if len(speeds) == 0:
            return speeds, 0, 0
        
        if len(speeds) == 0:
            return speeds, 0, 0
        
        # Use utility functions for outlier detection and interpolation
        outlier_mask = detect_outliers_iqr(speeds, iqr_multiplier, upper_only=True)
        outliers_detected = outlier_mask.sum()
        
        if outliers_detected > 0:
            processed_speeds = interpolate_outliers(speeds, outlier_mask, interpolation_method)
            return processed_speeds, int(outliers_detected), int(outliers_detected)
        
        return speeds, 0, 0
    
    def _calculate_speeds_with_window(self, df: pd.DataFrame, window_size: int) -> pd.Series:
        """
        Calculate speeds using specified window size
        
        Args:
            df: DataFrame with waypoints (lat, lon, timestamp columns)
            window_size: Window size (2=adjacent points, >2=moving average)
            
        Returns:
            Series of speeds in km/h
        """
        if len(df) < 2:
            return pd.Series([])
        
        # For window_size = 2 (adjacent points), use vectorized pandas operations
        if window_size == 2:
            # Calculate distances using vectorized operations
            lat1, lon1 = df['lat'].iloc[:-1], df['lon'].iloc[:-1]
            lat2, lon2 = df['lat'].iloc[1:], df['lon'].iloc[1:]
            
            distances = haversine_distance(lat1, lon1, lat2, lon2)
            
            # Calculate time differences
            time_diffs = df['timestamp'].diff().dt.total_seconds().iloc[1:]
            
            # Calculate speeds (avoid division by zero)
            speeds = safe_division((distances * 3.6), time_diffs, 0)
            
            return pd.Series(speeds)
        
        # For window_size > 2 (moving average approach)
        if len(df) < window_size:
            # Fall back to adjacent points if not enough data
            return self._calculate_speeds_with_window(df, 2)
        
        speeds = []
        
        for i in range(window_size, len(df)):
            point1 = df.iloc[i - window_size]
            point2 = df.iloc[i]
            
            # Calculate distance
            distance = haversine_distance(
                point1['lat'], point1['lon'],
                point2['lat'], point2['lon']
            )
            
            # Calculate time difference
            time_diff = (point2['timestamp'] - point1['timestamp']).total_seconds()
            
            if time_diff > 0:
                speed = (distance / time_diff) * 3.6
                speeds.append(speed)
        
        return pd.Series(speeds)

    
    def _generate_basic_statistics(self, waypoints: List[Dict]) -> Dict:
        """Generate basic statistics from raw waypoints"""
        if len(waypoints) < 2:
            return {
                'basic_metrics': {},
                'processing_methods': {},
                'results': {}
            }
        
        # Calculate basic metrics using pandas for efficiency
        df = pd.DataFrame(waypoints)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Total distance
        total_distance = self._calculate_total_distance(df)
        
        # Time information
        start_time = waypoints[0]['timestamp']
        end_time = waypoints[-1]['timestamp']
        
        # Duration calculation
        start_dt = pd.to_datetime(start_time)
        end_dt = pd.to_datetime(end_time)
        total_duration_seconds = (end_dt - start_dt).total_seconds()
        
        # Average speed
        avg_speed = (total_distance / (total_duration_seconds / 3600)) if total_duration_seconds > 0 else 0
        
        # Format duration as HH:MM:SS
        duration_formatted = format_duration(total_duration_seconds)
        
        return {
            'basic_metrics': {
                'start_time': start_time,
                'end_time': end_time,
                'total_distance': round(total_distance, 2),
                'total_duration': duration_formatted,
                'avg_speed': round(avg_speed, 2)
            },
            'processing_methods': {},
            'results': {}
        }
    
    def _calculate_total_distance(self, df: pd.DataFrame) -> float:
        """
        Calculate total distance using pandas vectorization
        
        Args:
            df: DataFrame with waypoints
            
        Returns:
            Total distance in kilometers
        """
        if len(df) < 2:
            return 0.0
        
        # Use vectorized distance calculation
        distances = haversine_distance(
            df['lat'].iloc[:-1], df['lon'].iloc[:-1],
            df['lat'].iloc[1:], df['lon'].iloc[1:]
        )
        
        return float(distances.sum() / 1000)  # Convert to kilometers