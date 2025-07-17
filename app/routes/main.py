"""
Main application routes
Handles home page, dashboard, and general navigation
"""

from flask import render_template, jsonify, session, url_for, redirect, flash, request
from app import app
from app.models import Track
from functools import wraps

# --------------------
# Login Required Decorator
# --------------------
def login_required(f):
    @wraps(f)
    def secure_route(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return secure_route


# --------------------
# Home Page (requires login)
# --------------------
@app.route('/')
@login_required
def index():
    """Home page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))


# --------------------
# User Dashboard (My Tracks)
# --------------------
@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing all tracks with simplified view"""
    user_id = session['user_id']
    tracks = Track.get_by_user(user_id)
    
    # Prepare simplified track data for display
    processed_tracks = []
    total_distance = 0
    
    if tracks:
        for track in tracks:
            print(f"Track {track['track_id']}: is_public = {track['is_public']} ({type(track['is_public'])})")
            stats = track.get('jsonb_statistics', {})
            basic_metrics = stats.get('basic_metrics', {})
            
            # Simplified track data - only essential fields
            track_data = {
                'track_id': track.get('track_id'),
                'track_name': track.get('track_name', 'Unknown'),
                'total_distance': basic_metrics.get('total_distance', 0),
                'total_duration': basic_metrics.get('total_duration', 'N/A'),
                'avg_speed': basic_metrics.get('avg_speed', 0),
                'is_public': track.get('is_public', False),
                'created_at': track.get('created_at')
            }
            
            processed_tracks.append(track_data)
            total_distance += track_data['total_distance']
    
    summary_stats = {
        'total_distance': total_distance,
        'total_tracks': len(processed_tracks)
    }
    
    return render_template('dashboard.html', tracks=processed_tracks, summary_stats=summary_stats)


# --------------------
# Toggle  private or public (My Tracks)
# --------------------
@app.route('/api/toggle_visibility/<int:track_id>', methods=['POST'])
@login_required
def api_toggle_visibility(track_id):
    user_id = session.get('user_id')
    track = Track.get_by_id(track_id)

    if not track or track.get('user_id') != user_id:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403

    current = track.get('is_public', False)
    Track.update_visibility(track_id, not current)

    return jsonify({
        'success': True,
        'is_public': not current,
        'track_id': track_id
    })


# --------------------
# Delete track (My Tracks)
# --------------------
@app.route('/delete_track/<int:track_id>', methods=['POST'])
@login_required
def delete_track(track_id):
    """Delete a user-owned track securely"""
    user_id = session.get('user_id')
    track = Track.get_by_id(track_id)

    if not track:
        flash("Track not found.")
        return redirect(url_for('dashboard'))

    if track.get('user_id') != user_id:
        flash("Permission denied.")
        return redirect(url_for('dashboard'))

    try:
        Track.delete_by_id(track_id, user_id)
        flash("Track deleted successfully.")
    except Exception as e:
        flash("Error deleting track.")
        print(f"Delete failed: {e}")

    return redirect(url_for('dashboard'))


# @app.route('/map_view/<int:track_id>')
# def map_view(track_id):
#     """Map view page - placeholder for teammate's development"""
#     return f"<h1>Map View for Track {track_id}</h1><p>This feature will be developed by teammates!</p>"


# --------------------
# Test DB Connection (Open)
# --------------------
@app.route('/test_db')
def test_db():
    """Test database connection and show basic info"""
    try:
        tracks = Track.get_by_user(1)
        return jsonify({
            'status': 'success',
            'message': 'Database connection working',
            'track_count': len(tracks) if tracks else 0
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        })


# --------------------
# Track Coordinate API (shared by My & Public Dashboard)
# -------------------- 
@app.route('/api/track_coords/<int:track_id>')
def get_track_coords(track_id):
    """Return waypoints (lat/lon) for the selected track"""
    track = Track.get_by_id(track_id)
    if not track:
        return jsonify({'error': 'Track not found'}), 404

    coords = track.get('jsonb_waypoints', [])

    simplified_coords = [{'lat': pt['lat'], 'lon': pt['lon']} for pt in coords]

    return jsonify({'coords': simplified_coords})


# --------------------
# Track Animation (shared by My & Public Dashboard)
# --------------------
@app.route('/animation/<int:track_id>', methods=['GET', 'POST'])
def track_animation(track_id):
    """Render track animation page for the given track ID"""
    source = request.args.get('source', 'my')
    return render_template('track_animation.html', track_id=track_id, source=source)


# --------------------
# Public Dashboard (Public Tracks)
# --------------------
@app.route('/dashboard_public')
def dashboard_public():
    """Public dashboard showing only tracks marked as public"""
    tracks = Track.get_by_public()
    
    # Prepare simplified track data for display
    processed_tracks = []
    total_distance = 0
    
    if tracks:
        for track in tracks:
            # Ensure we have a dictionary
            if not isinstance(track, dict):
                continue

            stats = track.get('jsonb_statistics', {})
            basic_metrics = stats.get('basic_metrics', {})
            
            # Simplified track data - only essential fields
            track_data = {
                'track_id': track.get('track_id'),
                'track_name': track.get('track_name', 'Unknown'),
                'username': track.get('username', 'Anonymous'),  # Add this line
                'total_distance': basic_metrics.get('total_distance', 0),
                'total_duration': basic_metrics.get('total_duration', 'N/A'),
                'avg_speed': basic_metrics.get('avg_speed', 0),
                'created_at': track.get('created_at')
            }
            
            processed_tracks.append(track_data)
            total_distance += track_data['total_distance']
    
    summary_stats = {
        'total_distance': total_distance,
        'total_tracks': len(processed_tracks)
    }
    
    return render_template('dashboard_public.html', tracks=processed_tracks, summary_stats=summary_stats)