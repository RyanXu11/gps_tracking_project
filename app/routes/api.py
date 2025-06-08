"""
API routes for AJAX requests and data retrieval
Handles JSON responses for frontend functionality using new three-field structure
"""

from flask import jsonify
import pytz
from app import app
from app.models import Track
from gpx_tools.gpx_processor import GPXProcessor
import pandas as pd

from gpx_tools.utils import DateTimeUtils
from gpx_tools.utils import detect_outliers_iqr, interpolate_outliers
from settings.constants import TIMEZONE_STR


@app.route('/api/user/<int:user_id>/tracks')
def get_user_tracks(user_id):
    """Get all tracks for a specific user"""
    tracks = Track.get_by_user(user_id)
    
    # Format tracks for API response
    formatted_tracks = []
    for track in tracks:
        statistics = track.get('jsonb_statistics', {})
        basic_metrics = statistics.get('basic_metrics', {})
        results = statistics.get('results', {})
        
        formatted_tracks.append({
            'track_id': track.get('track_id'),
            'track_name': track.get('track_name'),
            'description': track.get('description'),
            'created_at': track.get('created_at').isoformat() if track.get('created_at') else None,
            'total_distance': basic_metrics.get('total_distance', 0),
            'avg_speed': basic_metrics.get('avg_speed', 0),
            'max_speed': results.get('processed_max_speed', 0),
            'waypoint_count': len(track.get('jsonb_waypoints', [])),
            'has_processing': bool(statistics.get('processing_methods', {}))
        })
    
    return jsonify(formatted_tracks)


@app.route('/api/track/<int:track_id>/speeds')
def get_track_speeds(track_id):
    """Get speed data for track visualization using new structure"""
    try:
        track = Track.get_by_id(track_id)
        
        if not track or not track.get('jsonb_waypoints'):
            return jsonify({'error': 'No track data available'}), 404
        
        waypoints = track['jsonb_waypoints']
        statistics = track.get('jsonb_statistics', {})
        processing_methods = statistics.get('processing_methods', {})
        results = statistics.get('results', {})
        
        # Create processor instance
        processor = GPXProcessor()
        
        # Convert waypoints to DataFrame for speed calculations
        df = pd.DataFrame(waypoints)
        
        # Ensure timestamp is datetime type for speed calculations
        if 'timestamp' in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Get raw speeds (adjacent points method)
        raw_speeds = processor._calculate_speeds_with_window(df, 2)
        
        # Get processed speeds based on stored processing methods
        processed_speeds = raw_speeds.copy()
        
        if processing_methods.get('IQR_Outlier') or processing_methods.get('Moving_Average'):
            window_size = processing_methods.get('Window_Size', 2)
            
            # Recalculate with the stored window size
            if window_size > 2:
                processed_speeds = processor._calculate_speeds_with_window(df, window_size)
            
            # Apply IQR outlier detection if it was used
            if processing_methods.get('IQR_Outlier'):
                from gpx_tools.utils import detect_outliers_iqr, interpolate_outliers
                outlier_mask = detect_outliers_iqr(processed_speeds)
                interpolation_method = processing_methods.get('Interpolation_Method', 'linear')
                processed_speeds = interpolate_outliers(
                    processed_speeds, 
                    outlier_mask,
                    interpolation_method
                )
        
        # Create timestamps for chart display with Ottawa timezone
        if 'timestamp' in df.columns and not df['timestamp'].isna().all():
            from gpx_tools.utils import DateTimeUtils
            timestamps = DateTimeUtils.format_timestamps_for_chart(df['timestamp'])
        else:
            timestamps = [f"Point {i+1}" for i in range(len(raw_speeds))]
        
        return jsonify({
            'raw_speeds': raw_speeds.tolist() if hasattr(raw_speeds, 'tolist') else list(raw_speeds),
            'processed_speeds': processed_speeds.tolist() if hasattr(processed_speeds, 'tolist') else list(processed_speeds),
            'timestamps': timestamps,
            'waypoint_count': len(waypoints),
            'speed_samples': len(raw_speeds),
            'processing_methods': processing_methods,
            'statistics': {
                'raw_max_speed': results.get('raw_max_speed', float(raw_speeds.max()) if len(raw_speeds) > 0 else 0),
                'processed_max_speed': results.get('processed_max_speed', float(processed_speeds.max()) if len(processed_speeds) > 0 else 0),
                'outliers_detected': results.get('outliers_detected', 0),
                'outliers_interpolated': results.get('outliers_interpolated', 0),
                'data_points_remaining': results.get('data_points_remaining', len(processed_speeds))
            }
        })
        
    except Exception as e:
        print(f"Error in get_track_speeds: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/track/<int:track_id>/processing_info')
def get_track_processing_info(track_id):
    """Get detailed processing information for a track using new structure"""
    try:
        track = Track.get_by_id(track_id)
        
        if not track:
            return jsonify({'error': 'Track not found'}), 404
        
        # Extract data from new three-field structure
        statistics = track.get('jsonb_statistics', {})
        basic_metrics = statistics.get('basic_metrics', {})
        results = statistics.get('results', {})
        processing_methods = statistics.get('processing_methods', {})
        metadata = track.get('jsonb_metadata', {})
        
        return jsonify({
            'basic_metrics': basic_metrics,
            'results': results,
            'processing_methods': processing_methods,
            'metadata': metadata,
            'waypoint_count': len(track.get('jsonb_waypoints', [])),
            'data_quality': {
                'outliers_detected': results.get('outliers_detected', 0),
                'outliers_interpolated': results.get('outliers_interpolated', 0),
                'raw_max_speed': results.get('raw_max_speed', 0),
                'processed_max_speed': results.get('processed_max_speed', 0),
                'data_points_remaining': results.get('data_points_remaining', 0),
                'speed_improvement': results.get('raw_max_speed', 0) - results.get('processed_max_speed', 0)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/track/<int:track_id>/summary')
def get_track_summary(track_id):
    """Get track summary for dashboard cards using new structure"""
    try:
        track = Track.get_by_id(track_id)
        
        if not track:
            return jsonify({'error': 'Track not found'}), 404
        
        # Extract data from new structure
        statistics = track.get('jsonb_statistics', {})
        basic_metrics = statistics.get('basic_metrics', {})
        results = statistics.get('results', {})
        processing_methods = statistics.get('processing_methods', {})
        metadata = track.get('jsonb_metadata', {})
        waypoints = track.get('jsonb_waypoints', [])
        
        return jsonify({
            'track_id': track_id,
            'track_name': track.get('track_name', 'Unknown'),
            'description': track.get('description'),
            'created_at': track.get('created_at').isoformat() if track.get('created_at') else None,
            'total_distance': basic_metrics.get('total_distance', 0),
            'total_duration': basic_metrics.get('total_duration', '00:00:00'),
            'avg_speed': basic_metrics.get('avg_speed', 0),
            'max_speed': results.get('processed_max_speed', results.get('raw_max_speed', 0)),
            'waypoint_count': len(waypoints),
            'metadata_waypoint_count': metadata.get('waypoint_count', 0),
            'device_info': {
                'creator': metadata.get('creator', 'Unknown'),
                'software': metadata.get('software', 'Unknown')
            },
            'processing_info': {
                'has_processing': bool(processing_methods),
                'iqr_outlier': processing_methods.get('IQR_Outlier', False),
                'moving_average': processing_methods.get('Moving_Average', False),
                'window_size': processing_methods.get('Window_Size', 2),
                'interpolation_method': processing_methods.get('Interpolation_Method', 'linear'),
                'outliers_detected': results.get('outliers_detected', 0)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/track/<int:track_id>/waypoints')
def get_track_waypoints(track_id):
    """Get waypoints data for map visualization"""
    try:
        track = Track.get_by_id(track_id)
        
        if not track:
            return jsonify({'error': 'Track not found'}), 404
        
        waypoints = track.get('jsonb_waypoints', [])
        metadata = track.get('jsonb_metadata', {})
        
        # Limit waypoints for performance (optional)
        limit = 1000  # Adjust based on frontend needs
        if len(waypoints) > limit:
            # Sample waypoints evenly
            step = len(waypoints) // limit
            sampled_waypoints = waypoints[::step]
        else:
            sampled_waypoints = waypoints
        
        return jsonify({
            'waypoints': sampled_waypoints,
            'total_waypoints': len(waypoints),
            'sampled_waypoints': len(sampled_waypoints),
            'metadata': metadata,
            'bounds': {
                'min_lat': min(wp['lat'] for wp in waypoints) if waypoints else 0,
                'max_lat': max(wp['lat'] for wp in waypoints) if waypoints else 0,
                'min_lon': min(wp['lon'] for wp in waypoints) if waypoints else 0,
                'max_lon': max(wp['lon'] for wp in waypoints) if waypoints else 0
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/track/<int:track_id>/statistics')
def get_track_statistics(track_id):
    """Get complete statistics for a track"""
    try:
        track = Track.get_by_id(track_id)
        
        if not track:
            return jsonify({'error': 'Track not found'}), 404
        
        return jsonify({
            'track_id': track_id,
            'track_name': track.get('track_name'),
            'statistics': track.get('jsonb_statistics', {}),
            'metadata': track.get('jsonb_metadata', {}),
            'waypoint_count': len(track.get('jsonb_waypoints', []))
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/<int:user_id>/statistics')
def get_user_statistics(user_id):
    """Get aggregated statistics for all user tracks"""
    try:
        tracks = Track.get_by_user(user_id)
        
        if not tracks:
            return jsonify({'error': 'No tracks found for user'}), 404
        
        # Aggregate statistics
        total_tracks = len(tracks)
        total_distance = 0
        total_outliers = 0
        processing_methods_usage = {
            'iqr_outlier': 0,
            'moving_average': 0
        }
        
        for track in tracks:
            statistics = track.get('jsonb_statistics', {})
            basic_metrics = statistics.get('basic_metrics', {})
            results = statistics.get('results', {})
            processing_methods = statistics.get('processing_methods', {})
            
            # Accumulate metrics
            total_distance += basic_metrics.get('total_distance', 0)
            total_outliers += results.get('outliers_detected', 0)
            
            # Count processing method usage
            if processing_methods.get('IQR_Outlier'):
                processing_methods_usage['iqr_outlier'] += 1
            if processing_methods.get('Moving_Average'):
                processing_methods_usage['moving_average'] += 1
        
        return jsonify({
            'user_id': user_id,
            'total_tracks': total_tracks,
            'total_distance': total_distance,
            'avg_distance': total_distance / total_tracks if total_tracks > 0 else 0,
            'total_outliers_detected': total_outliers,
            'avg_outliers_per_track': total_outliers / total_tracks if total_tracks > 0 else 0,
            'processing_methods_usage': processing_methods_usage,
            'processing_usage_percentage': {
                'iqr_outlier': (processing_methods_usage['iqr_outlier'] / total_tracks) * 100 if total_tracks > 0 else 0,
                'moving_average': (processing_methods_usage['moving_average'] / total_tracks) * 100 if total_tracks > 0 else 0
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500