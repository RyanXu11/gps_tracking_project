"""
Refactored from track.py, focuses on speed-related logic only
"""
import math
import pandas as pd
from flask import render_template, request, jsonify, flash, redirect, url_for
from app import app
from app.models import Track
from gpx_tools.gpx_processor import GPXProcessor
from gpx_tools.utils import DateTimeUtils, validate_complete_gpx_data
from gpx_tools.utils import detect_outliers_iqr, interpolate_outliers
from urllib.parse import urlparse, parse_qs


def get_source_from_referrer():
    ref = request.referrer or ''
    parsed = urlparse(ref)
    query = parse_qs(parsed.query)
    return query.get('source', ['my'])[0]  # default is 'my'


def safe_float(value, default=0.0, decimals=None):
    try:
        result = float(value) if value is not None else default
        if decimals is not None:
            return round(result, decimals)
        return result
    except (ValueError, TypeError):
        return default


def clean_series_for_json(series):
    return [0 if (isinstance(x, float) and (math.isnan(x) or math.isinf(x))) else x for x in series]


def ensure_timestamp(df):
    if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


def calculate_speeds(df, methods):
    processor = GPXProcessor()
    raw = processor._calculate_speeds_with_window(df, 2)
    base = processor._calculate_speeds_with_window(df, methods.get('Window_Size', 2))
    processed = base.copy()

    outliers_detected = 0
    outliers_interpolated = 0

    if methods.get('IQR_Outlier'):
        mask = detect_outliers_iqr(processed)
        outliers_detected = int(mask.sum())
        processed[mask] = float('nan')
        interpolation_method = methods.get('Interpolation_Method', 'linear')
        processed = processed.interpolate(method=interpolation_method)
        outliers_interpolated = outliers_detected

    if methods.get('Moving_Average') and methods.get('Window_Size', 2) > 2:
        processed = processor._calculate_speeds_with_window(df, methods.get('Window_Size', 2))

    # Bug fix: if first value still NaN after interpolation, use nearest valid value
    if processed.notna().any():  
        processed = processed.bfill()
    else:
        processed = processed.fillna(0.0)

    print(f"[DEBUG] After bfill - processed_speeds[:5]:\n{processed[:5]}")
                
    return raw, processed


@app.route('/speed_chart/<int:track_id>', methods=['GET', 'POST'])
def speed_chart(track_id):
    source = request.args.get('source', 'my')

    if request.method == 'GET':
        return render_speed_chart(track_id, source)
    else:
        return handle_speed_reprocessing(track_id)


def render_speed_chart(track_id, source):
    track = Track.get_by_id(track_id)
    if not track:
        flash('Track not found')
        return redirect(url_for('dashboard' if source == 'my' else 'dashboard_public'))

    statistics = track.get('jsonb_statistics', {})
    settings = statistics.get('processing_methods', {})
    basic = statistics.get('basic_metrics', {})
    results = statistics.get('results', {})

    current = {
        'use_iqr': settings.get('IQR_Outlier', False),
        'window_size': settings.get('Window_Size', 2),
        'interpolation_method': settings.get('Interpolation_Method', 'linear'),
        'outliers_detected': results.get('outliers_detected', 0),
        'processed_max_speed': results.get('processed_max_speed', 0),
        'raw_max_speed': results.get('raw_max_speed', 0)
    }

    return render_template('speed_chart.html',
                           track=track,
                           current_settings=current,
                           basic_metrics=basic,
                           results=results,
                           source=source)


def handle_speed_reprocessing(track_id):
    source = get_source_from_referrer()

    use_iqr = request.form.get('use_iqr') == 'on'
    window_size = int(request.form.get('window_size', 2))
    interpolation_method = request.form.get('interpolation_method', 'linear')

    try:
        track = Track.get_by_id(track_id)
        if not track or not track.get('gpx_file'):
            return jsonify({'success': False, 'error': 'Track not found or no GPX data available'}), 404

        waypoints = track.get('jsonb_waypoints', [])
        if not waypoints:
            processor = GPXProcessor()
            gpx_content = track['gpx_file'].decode('utf-8')
            waypoints = processor.parse_gpx(gpx_content)['jsonb_waypoints']

        processor = GPXProcessor()
        stats = processor.process_with_methods(waypoints, use_iqr, window_size, interpolation_method)

        try:
            metadata = track.get('jsonb_metadata', {})
            validate_complete_gpx_data(waypoints, metadata, stats)
        except Exception as validation_error:
            print(f"Validation warning: {validation_error}")

        Track.update_statistics(track_id, stats)

        updated = Track.get_by_id(track_id).get('jsonb_statistics', {})
        basic = updated.get('basic_metrics', {})
        results = updated.get('results', {})

        msg_parts = []
        if use_iqr:
            msg_parts.append(f"IQR outlier detection ({results.get('outliers_detected', 0)} outliers found)")
        if window_size > 2:
            msg_parts.append(f"Moving average (window: {window_size})")
        if interpolation_method != 'linear':
            msg_parts.append(f"Interpolation: {interpolation_method}")
        msg = f" Applied: {', '.join(msg_parts)}" if msg_parts else ""

        return jsonify({
            'success': True,
            'track_id': track_id,
            'statistics': {
                'avg_speed': round(safe_float(basic.get('avg_speed', 0)), 2),
                'data_points_remaining': results.get('data_points_remaining', 0),
                'outliers_detected': results.get('outliers_detected', 0),
                'outliers_interpolated': results.get('outliers_interpolated', 0),
                'processed_max_speed': round(safe_float(results.get('processed_max_speed', 0)), 2),
                'raw_max_speed': safe_float(results.get('raw_max_speed', 0), decimals=2),
                'total_distance': float(basic.get('total_distance', 0)),
                'waypoint_count': len(waypoints)
            },
            'processing_methods': {
                'use_iqr': use_iqr,
                'window_size': window_size,
                'interpolation_method': interpolation_method
            },
            'message': f'Track reprocessed successfully!{msg}',
            'actions': {
                'dashboard_url': url_for('dashboard' if source == 'my' else 'dashboard_public'),
                'speed_chart': url_for('speed_chart', track_id=track_id) + f'?source={source}'
            }
        })

    except Exception as e:
        print(f"Reprocessing error: {e}")
        return jsonify({'success': False, 'error': f'Error reprocessing track: {str(e)}'}), 500


@app.route('/api/track/<int:track_id>/speeds')
def get_track_speeds(track_id):
    try:
        track = Track.get_by_id(track_id)
        if not track or not track.get('jsonb_waypoints'):
            return jsonify({'error': 'No track data available'}), 404

        waypoints = track['jsonb_waypoints']
        stats = track.get('jsonb_statistics', {})
        methods = stats.get('processing_methods', {})
        results = stats.get('results', {})

        df = pd.DataFrame(waypoints)
        df = ensure_timestamp(df)
        raw, processed = calculate_speeds(df, methods)

        timestamps = DateTimeUtils.format_timestamps_for_chart(df['timestamp']) if 'timestamp' in df.columns and not df['timestamp'].isna().all() else [f"Point {i+1}" for i in range(len(raw))]

        return jsonify({
            'raw_speeds': clean_series_for_json(raw),
            'processed_speeds': clean_series_for_json(processed),
            'timestamps': timestamps,
            'waypoint_count': len(waypoints),
            'speed_samples': len(raw),
            'processing_methods': methods,
            'statistics': {
                'raw_max_speed': results.get('raw_max_speed', float(raw.max()) if len(raw) > 0 else 0),
                'processed_max_speed': results.get('processed_max_speed', float(processed.max()) if len(processed) > 0 else 0),
                'outliers_detected': results.get('outliers_detected', 0),
                'outliers_interpolated': results.get('outliers_interpolated', 0),
                'data_points_remaining': results.get('data_points_remaining', len(processed))
            }
        })

    except Exception as e:
        print(f"[ERROR] get_track_speeds: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500