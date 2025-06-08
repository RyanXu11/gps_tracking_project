"""
Track processing and reprocessing routes
Handles track parameter adjustment and reprocessing
"""

from flask import render_template, request, jsonify, flash, redirect, url_for
from app import app
from app.models import Track
from gpx_tools.gpx_processor import GPXProcessor
from gpx_tools.utils import validate_complete_gpx_data


@app.route('/speed_chart/<int:track_id>', methods=['GET', 'POST'])
def speed_chart(track_id):
    """Reprocess track with different processing methods using new three-field structure"""
    if request.method == 'GET':
        # Get track info for display
        track = Track.get_by_id(track_id)
        if not track:
            flash('Track not found')
            return redirect(url_for('dashboard'))
        
        # Get current processing settings from new structure
        statistics = track.get('jsonb_statistics', {})
        current_settings = statistics.get('processing_methods', {})
        basic_metrics = statistics.get('basic_metrics', {})
        results = statistics.get('results', {})
        
        # Prepare current settings for template
        current_processing = {
            'use_iqr': current_settings.get('IQR_Outlier', False),
            'window_size': current_settings.get('Window_Size', 2),
            'interpolation_method': current_settings.get('Interpolation_Method', 'linear'),
            'outliers_detected': results.get('outliers_detected', 0),
            'processed_max_speed': results.get('processed_max_speed', 0),
            'raw_max_speed': results.get('raw_max_speed', 0)
        }
        
        return render_template('speed_chart.html', 
                             track=track, 
                             current_settings=current_processing,
                             basic_metrics=basic_metrics,
                             results=results)
    
    # POST method - handle reprocessing
    use_iqr = request.form.get('use_iqr') == 'on'
    window_size = int(request.form.get('window_size', 2))
    interpolation_method = request.form.get('interpolation_method', 'linear')
    
    print(f"Reprocessing track {track_id} with: IQR={use_iqr}, Window={window_size}, Interpolation={interpolation_method}")
    
    try:
        # Get track with GPX data
        track = Track.get_by_id(track_id)
        if not track or not track.get('gpx_file'):
            return jsonify({
                'success': False,
                'error': 'Track not found or no GPX data available'
            }), 404
        
        try:
            # Option 1: Reprocess from stored waypoints (recommended for performance)
            waypoints = track.get('jsonb_waypoints', [])
            if not waypoints:
                # Option 2: Fallback to reparse if waypoints not available
                print("No stored waypoints found, reparsing GPX file...")
                processor = GPXProcessor()
                gpx_content = track['gpx_file'].decode('utf-8')
                parse_result = processor.parse_gpx(gpx_content)
                waypoints = parse_result['jsonb_waypoints']
            
            print(f"Processing {len(waypoints)} waypoints")
            
            # Apply new processing methods using stored waypoints
            processor = GPXProcessor()
            new_statistics = processor.process_with_methods(
                waypoints=waypoints,
                use_iqr=use_iqr,
                window_size=window_size,
                interpolation_method=interpolation_method
            )
            
            print(f"New statistics generated: {list(new_statistics.keys())}")
            
            # Validate the new statistics
            try:
                metadata = track.get('jsonb_metadata', {})
                validate_complete_gpx_data(waypoints, metadata, new_statistics)
                print("Reprocessing validation passed")
            except Exception as validation_error:
                print(f"Validation warning during reprocessing: {validation_error}")
                # Continue processing even with validation warnings
            
            # Update track record with new statistics only
            print("STEP: updating track")
            Track.update_statistics(track_id, new_statistics)
            
            # Get updated track data
            updated_track = Track.get_by_id(track_id)
            updated_stats = updated_track.get('jsonb_statistics', {})
            updated_results = updated_stats.get('results', {})
            updated_basic = updated_stats.get('basic_metrics', {})
            print(f"updated_stats: {updated_stats}")
            
            # Build processing info message
            processing_info = []
            if use_iqr:
                outliers_count = updated_results.get('outliers_detected', 0)
                processing_info.append(f"IQR outlier detection ({outliers_count} outliers found)")
            if window_size > 2:
                processing_info.append(f"Moving average (window: {window_size})")
            if interpolation_method != 'linear':
                processing_info.append(f"Interpolation: {interpolation_method}")
            
            processing_msg = f" Applied: {', '.join(processing_info)}" if processing_info else ""
            
            print(f"processed_max_speed: {updated_results.get('processed_max_speed', 0)}")
            # Return JSON response for AJAX with updated data
            return jsonify({
                'success': True,
                'track_id': track_id,
                'statistics': {
                    'avg_speed': round(safe_float(updated_basic.get('avg_speed', 0)), 2),
                    'data_points_remaining': updated_results.get('data_points_remaining', 0),     
                    'outliers_detected': updated_results.get('outliers_detected', 0),
                    'outliers_interpolated': updated_results.get('outliers_interpolated', 0),                                   
                    'processed_max_speed': round(safe_float(updated_results.get('processed_max_speed', 0)), 2),
                    'raw_max_speed': safe_float(updated_results.get('raw_max_speed', 0), decimals=2),
                    'total_distance': float(updated_basic.get('total_distance', 0)),
                    'waypoint_count': len(waypoints)
                },
                'processing_methods': {
                    'use_iqr': use_iqr,
                    'window_size': window_size,
                    'interpolation_method': interpolation_method
                },
                'message': f'Track reprocessed successfully!{processing_msg}',
                'actions': {
                    'dashboard_url': url_for('dashboard'),
                    'speed_chart': url_for('speed_chart', track_id=track_id),
                    # 'view_track_url': url_for('view_track', track_id=track_id)
                }
            })
            
        except Exception as e:
            print(f"Reprocessing error: {e}")
            return jsonify({
                'success': False,
                'error': f'Error reprocessing track: {str(e)}'
            }), 500
        
    except Exception as e:
        print(f"Track access error: {e}")
        return jsonify({
            'success': False,
            'error': f'Error accessing track: {str(e)}'
        }), 500

def safe_float(value, default=0.0, decimals=None):
    try:
        result = float(value) if value is not None else default
        if decimals is not None:
            return round(result, decimals)
        return result
    except (ValueError, TypeError):
        return default


@app.route('/api/track_data/<int:track_id>')
def api_track_data(track_id):
    """API endpoint to get track data in JSON format"""
    track = Track.get_by_id(track_id)
    if not track:
        return jsonify({'error': 'Track not found'}), 404
    
    # Return structured track data
    return jsonify({
        'track_id': track_id,
        'track_name': track.get('track_name'),
        'waypoints': track.get('jsonb_waypoints', []),
        'metadata': track.get('jsonb_metadata', {}),
        'statistics': track.get('jsonb_statistics', {}),
        'created_at': track.get('created_at').isoformat() if track.get('created_at') else None
    })