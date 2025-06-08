"""
Common utility functions for GPX processing
"""

import math
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Union, Optional, List, Dict

import pytz

from settings.constants import TIMEZONE_STR

class DateTimeUtils:
    """DateTime utility functions"""
    
    @staticmethod
    def parse_iso_datetime(datetime_str: str) -> datetime:
        """
        Parse ISO datetime string to datetime object
        
        Args:
            datetime_str: ISO format datetime string
            
        Returns:
            datetime object
            
        Raises:
            ValueError: If datetime format is invalid
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
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Format duration in seconds to HH:MM:SS string
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string (HH:MM:SS)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def parse_duration(duration_str: str) -> float:
        """
        Parse HH:MM:SS duration string to seconds
        
        Args:
            duration_str: Duration string in HH:MM:SS format
            
        Returns:
            Duration in seconds
        """
        try:
            parts = duration_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            else:
                raise ValueError("Duration must be in HH:MM:SS format")
        except Exception as e:
            raise ValueError(f"Invalid duration format: {duration_str}")
    
    @staticmethod
    def convert_timestamps_to_ottawa(timestamps_series):
        """
        Convert timestamps to Ottawa timezone
        
        Args:
            timestamps_series: pandas Series with datetime values
            
        Returns:
            pandas Series with Ottawa timezone timestamps
        """        
        ottawa_tz = pytz.timezone(TIMEZONE_STR)
        
        # Ensure datetime type
        if not pd.api.types.is_datetime64_any_dtype(timestamps_series):
            timestamps_series = pd.to_datetime(timestamps_series)
        
        # If no timezone info, assume UTC
        if timestamps_series.dt.tz is None:
            timestamps_series = timestamps_series.dt.tz_localize('UTC')
        
        # Convert to Ottawa timezone
        return timestamps_series.dt.tz_convert(ottawa_tz)

    @staticmethod
    def format_timestamps_for_chart(timestamps_series, format='%I:%M %p'):
        """
        Format timestamps for chart display
        
        Args:
            timestamps_series: pandas Series with datetime values
            format: strftime format string (default: '%I:%M %p' for 12-hour + AM/PM)
            
        Returns:
            list of formatted timestamp strings in Ottawa timezone
        """
        ottawa_timestamps = DateTimeUtils.convert_timestamps_to_ottawa(timestamps_series)
        return ottawa_timestamps.dt.strftime(format).tolist()

class GeospatialUtils:
    """Geospatial utility functions"""
    
    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points on Earth using Haversine formula
        Supports both single values and pandas Series (vectorized)
        
        Args:
            lat1, lon1: First point coordinates (degrees) - float or pd.Series
            lat2, lon2: Second point coordinates (degrees) - float or pd.Series
            
        Returns:
            Distance in meters - float or pd.Series
        """
        # Earth radius in meters
        earth_radius = 6371000
        
        # Check if inputs are pandas Series (vectorized) or single values
        is_vectorized = isinstance(lat1, pd.Series)
        
        if is_vectorized:
            # Vectorized calculation using numpy
            lat1, lon1, lat2, lon2 = np.radians([lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
            c = 2 * np.arcsin(np.sqrt(a))
            
            return earth_radius * c
        else:
            # Single value calculation using math
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            return earth_radius * c


class DataProcessingUtils:
    """Data processing utility functions"""
    
    def detect_outliers_iqr(data, multiplier=1.5, upper_only=True):
        """
        Detect outliers using IQR method
        
        Args:
            data: pandas Series of values
            multiplier: IQR multiplier (default: 1.5)
            upper_only: If True, only detect upper outliers (recommended for speed data)
            
        Returns:
            Boolean mask indicating outliers
        """
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        
        if upper_only:
            # Only detect unreasonably high speeds
            upper_bound = Q3 + multiplier * IQR
            return data > upper_bound
        else:
            # Traditional two-sided detection
            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR
            return (data < lower_bound) | (data > upper_bound)
    
    @staticmethod
    def interpolate_outliers(data: pd.Series, outlier_mask: pd.Series, 
                           method: str = 'linear') -> pd.Series:
        """
        Interpolate outliers in data series
        
        Args:
            data: Original data series
            outlier_mask: Boolean series indicating outliers
            method: Interpolation method
            
        Returns:
            Data series with outliers interpolated: Linear, Quadratic, Nearest
        """
        # Create a copy and mark outliers as NaN
        processed_data = data.copy()
        processed_data.loc[outlier_mask] = np.nan
        
        # Interpolate NaN values
        return processed_data.interpolate(method=method)
    
    @staticmethod
    def safe_division(numerator: Union[float, pd.Series], 
                     denominator: Union[float, pd.Series], 
                     default: float = 0.0) -> Union[float, pd.Series]:
        """
        Safe division that handles division by zero
        
        Args:
            numerator: Numerator value(s)
            denominator: Denominator value(s)
            default: Default value when denominator is zero
            
        Returns:
            Division result(s) with zero denominators replaced by default
        """
        if isinstance(denominator, pd.Series):
            return np.where(denominator != 0, numerator / denominator, default)
        else:
            return numerator / denominator if denominator != 0 else default


class ValidationUtils:
    """Validation utility functions"""
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> bool:
        """
        Validate GPS coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            True if coordinates are valid
        """
        return (-90 <= lat <= 90) and (-180 <= lon <= 180)
    
    @staticmethod
    def validate_speed(speed: float, max_reasonable_speed: float = 300.0) -> bool:
        """
        Validate speed value
        
        Args:
            speed: Speed in km/h
            max_reasonable_speed: Maximum reasonable speed in km/h
            
        Returns:
            True if speed is reasonable
        """
        return 0 <= speed <= max_reasonable_speed
    
    @staticmethod
    def validate_dataframe_columns(df: pd.DataFrame, required_columns: list) -> bool:
        """
        Validate that DataFrame has required columns
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            True if all required columns exist
            
        Raises:
            ValueError: If required columns are missing
        """
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        return True


class GPXValidationUtils:
    """GPX-specific validation utility functions"""
    
    @staticmethod
    def validate_waypoints_structure(waypoints: List[Dict]) -> bool:
        """
        Validate waypoints list structure and data quality
        
        Args:
            waypoints: List of waypoint dictionaries
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(waypoints, list):
            raise ValueError("Waypoints must be a list")
        
        if len(waypoints) == 0:
            raise ValueError("Waypoints list cannot be empty")
        
        required_fields = ['lat', 'lon']
        optional_fields = ['timestamp', 'elevation']
        
        for i, waypoint in enumerate(waypoints):
            if not isinstance(waypoint, dict):
                raise ValueError(f"Waypoint {i} must be a dictionary")
            
            # Check required fields
            for field in required_fields:
                if field not in waypoint:
                    raise ValueError(f"Waypoint {i} missing required field: {field}")
            
            # Validate coordinates
            try:
                lat, lon = float(waypoint['lat']), float(waypoint['lon'])
                if not ValidationUtils.validate_coordinates(lat, lon):
                    raise ValueError(f"Waypoint {i} has invalid coordinates: lat={lat}, lon={lon}")
            except (ValueError, TypeError):
                raise ValueError(f"Waypoint {i} has invalid coordinate format")
            
            # Validate optional fields if present
            if 'elevation' in waypoint and waypoint['elevation'] is not None:
                try:
                    elevation = float(waypoint['elevation'])
                    if not (-1000 <= elevation <= 10000):  # Reasonable elevation range
                        raise ValueError(f"Waypoint {i} has unreasonable elevation: {elevation}m")
                except (ValueError, TypeError):
                    raise ValueError(f"Waypoint {i} has invalid elevation format")
        
        return True
    
    @staticmethod
    def validate_metadata_structure(metadata: Dict) -> bool:
        """
        Validate metadata object structure
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")
        
        # Check waypoint count consistency
        if 'waypoint_count' in metadata:
            try:
                count = int(metadata['waypoint_count'])
                if count < 0:
                    raise ValueError("Waypoint count cannot be negative")
            except (ValueError, TypeError):
                raise ValueError("Waypoint count must be a valid integer")
        
        return True
    
    @staticmethod
    def validate_statistics_structure(statistics: Dict) -> bool:
        """
        Validate statistics object structure
        
        Args:
            statistics: Statistics dictionary
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(statistics, dict):
            raise ValueError("Statistics must be a dictionary")
        
        required_sections = ['basic_metrics', 'processing_methods', 'results']
        for section in required_sections:
            if section not in statistics:
                raise ValueError(f"Missing required statistics section: {section}")
            
            if not isinstance(statistics[section], dict):
                raise ValueError(f"Statistics section '{section}' must be a dictionary")
        
        # Validate basic metrics
        basic_metrics = statistics['basic_metrics']
        numeric_fields = ['total_distance', 'avg_speed']
        for field in numeric_fields:
            if field in basic_metrics:
                try:
                    value = float(basic_metrics[field])
                    if value < 0:
                        raise ValueError(f"Basic metric '{field}' cannot be negative: {value}")
                except (ValueError, TypeError):
                    raise ValueError(f"Basic metric '{field}' must be a valid number")
        
        # Validate results
        results = statistics['results']
        speed_fields = ['raw_max_speed', 'processed_max_speed']
        for field in speed_fields:
            if field in results:
                try:
                    speed = float(results[field])
                    if not ValidationUtils.validate_speed(speed):
                        raise ValueError(f"Unreasonable speed in results '{field}': {speed} km/h")
                except (ValueError, TypeError):
                    raise ValueError(f"Results field '{field}' must be a valid number")
        
        return True
    
    @staticmethod
    def validate_complete_gpx_data(waypoints: List[Dict], metadata: Dict, statistics: Dict) -> bool:
        """
        Validate complete GPX data structure
        
        Args:
            waypoints: Waypoints list
            metadata: Metadata dictionary
            statistics: Statistics dictionary
            
        Returns:
            True if all validations pass
        """
        GPXValidationUtils.validate_waypoints_structure(waypoints)
        GPXValidationUtils.validate_metadata_structure(metadata)
        GPXValidationUtils.validate_statistics_structure(statistics)
        
        # Cross-validation: waypoint count consistency
        if 'waypoint_count' in metadata:
            expected_count = int(metadata['waypoint_count'])
            actual_count = len(waypoints)
            if expected_count != actual_count:
                raise ValueError(f"Waypoint count mismatch: metadata says {expected_count}, actual {actual_count}")
        
        return True


# Convenience function exports
parse_iso_datetime = DateTimeUtils.parse_iso_datetime
format_duration = DateTimeUtils.format_duration
haversine_distance = GeospatialUtils.haversine_distance
validate_coordinates = ValidationUtils.validate_coordinates
detect_outliers_iqr = DataProcessingUtils.detect_outliers_iqr
interpolate_outliers = DataProcessingUtils.interpolate_outliers
safe_division = DataProcessingUtils.safe_division

# GPX validation exports
validate_waypoints_structure = GPXValidationUtils.validate_waypoints_structure
validate_metadata_structure = GPXValidationUtils.validate_metadata_structure
validate_statistics_structure = GPXValidationUtils.validate_statistics_structure
validate_complete_gpx_data = GPXValidationUtils.validate_complete_gpx_data