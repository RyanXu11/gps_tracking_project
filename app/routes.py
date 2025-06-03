from datetime import datetime
from flask import render_template, jsonify, request, redirect, url_for, flash, json
from werkzeug.utils import secure_filename
import os
import hashlib
import tempfile
from app import app
from app.models import Track
from settings.constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from gpx_tools.gpx_processor import GPXProcessor
from gpx_tools.gpx_converter import GPXConverter


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/user/<int:user_id>/tracks')
def get_user_tracks(user_id):
    tracks = Track.get_by_user(user_id)
    return jsonify(tracks)


@app.route('/dashboard')
def dashboard():
    user_id = 1  # currently for debugging only
    tracks = Track.get_by_user(user_id)
    return render_template('dashboard.html', tracks=tracks)


def calculate_file_hash(file_content):
    """Calculate MD5 hash of file content"""
    hash_md5 = hashlib.md5()
    hash_md5.update(file_content)
    return hash_md5.hexdigest()


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        return render_template('upload.html')
    
    # POST method - handle file upload
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    username = request.form.get('username', 'temp')  # default to temp for testing
    skip_points = int(request.form.get('skip_points', 0))  # default to 0
    
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        try:
            # Read file content into memory
            file_content = file.read()
            file_hash = calculate_file_hash(file_content)
            print(f"File hash calculated: {file_hash}")
            print(f"Skip points setting: {skip_points}")
            
            # Check for duplicate files in database
            user_id = 1  # currently for debugging only
            if Track.check_duplicate_by_hash(user_id, file_hash):
                flash('File already exists! This GPX file has been uploaded before.')
                return redirect(request.url)
            
            # Create temporary file for GPX processing
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.gpx', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Process GPX file with specified skip_points
                processor = GPXProcessor()
                processed_data = processor.parse_gpx_file(temp_file_path, skip_points)
                
                # Convert to JSONB format
                converter = GPXConverter()
                converted_data = converter.convert_to_jsonb(processed_data)
                
                # Create track record in database (with file content)
                track_name = os.path.splitext(filename)[0]  # use filename without extension
                
                track_id = Track.create_with_gpx_data(
                    user_id=user_id,
                    track_name=track_name,
                    jsonb_data=converted_data['jsonb_track_data'],
                    extracted_fields=converted_data['extracted_fields'],
                    gpx_file_content=file_content,  # Store file content directly
                    file_hash=file_hash,
                    skip_points=skip_points
                )
                
                flash(f'File uploaded and processed successfully! Track ID: {track_id} (Sampling: {skip_points+1}-second intervals)')
                return redirect(url_for('dashboard'))
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            
        except Exception as e:
            flash(f'Error processing GPX file: {str(e)}')
            return redirect(request.url)
    
    else:
        flash('Invalid file type. Only GPX files are allowed.')
        return redirect(request.url)


@app.route('/recalculate/<int:track_id>', methods=['GET', 'POST'])
def recalculate_track(track_id):
    """Recalculate track statistics with different skip_points"""
    if request.method == 'GET':
        # Get track info for display
        track = Track.get_by_id(track_id)
        if not track:
            flash('Track not found')
            return redirect(url_for('dashboard'))
        return render_template('recalculate.html', track=track)
    
    # POST method - handle recalculation
    skip_points = int(request.form.get('skip_points', 1))
    
    try:
        # Get track with GPX data
        track = Track.get_by_id(track_id)
        if not track or not track.get('gpx_file'):
            flash('Track not found or no GPX data available')
            return redirect(url_for('dashboard'))
        
        # Create temporary file from stored GPX data
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.gpx', delete=False) as temp_file:
            temp_file.write(track['gpx_file'])
            temp_file_path = temp_file.name
        
        try:
            # Reprocess GPX file with new skip_points
            processor = GPXProcessor()
            processed_data = processor.parse_gpx_file(temp_file_path, skip_points)
            
            # Convert to JSONB format
            converter = GPXConverter()
            converted_data = converter.convert_to_jsonb(processed_data)
            
            # Update track record with new statistics
            Track.update_statistics(
                track_id=track_id,
                jsonb_data=converted_data['jsonb_track_data'],
                extracted_fields=converted_data['extracted_fields'],
                skip_points=skip_points
            )
            
            flash(f'Track recalculated successfully with {skip_points+1}-second intervals!')
            return redirect(url_for('dashboard'))
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
    except Exception as e:
        flash(f'Error recalculating track: {str(e)}')
        return redirect(url_for('dashboard'))


@app.route('/api/track/<int:track_id>/speeds')
def get_track_speeds(track_id):
    try:
        track = Track.get_by_id(track_id)       # return RealDictRow object
        
        if not track['jsonb_track_data']:
            return jsonify({'error': 'No track data available'}), 404
        
        waypoints = track['jsonb_track_data']['waypoints']
        skip_points = track['skip_points']
        
        processor = GPXProcessor()
        stats = processor._calculate_track_statistics(waypoints, skip_points)
        
        return jsonify({
            'speeds': stats.get('raw_speeds', []),
            'timestamps': [f"Point {i}" for i in range(len(stats.get('raw_speeds', [])))],
            'waypoint_count': stats.get('waypoint_count', 0),
            'speed_samples': stats.get('speed_samples', 0)
        })
        
        # For debug
        #return jsonify({
        #    'speeds': [10, 20, 30],
        #    'timestamps': ['A', 'B', 'C']
        #})
        
    except Exception as e:
        print(f"Error in get_track_speeds: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


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


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        