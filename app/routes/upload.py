"""
File upload and processing routes
Handles GPX file upload, processing, and success pages
"""

import os
import hashlib
from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

from app import app
from app.models import Track
from settings.constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from gpx_tools.gpx_processor import GPXProcessor
from gpx_tools.utils import validate_complete_gpx_data


def calculate_file_hash(file_content):
    """Calculate MD5 hash of file content"""
    hash_md5 = hashlib.md5()
    hash_md5.update(file_content)
    return hash_md5.hexdigest()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle GPX file upload with default processing"""
    if request.method == 'GET':
        return render_template('upload.html')
    
    # POST method - handle file upload
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    username = request.form.get('username', 'temp')  # default to temp for testing
    
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if not (file and allowed_file(file.filename)):
        flash('Invalid file type. Only GPX files are allowed.')
        return redirect(request.url)
    
    filename = secure_filename(file.filename)
    
    try:
        # Read file content into memory
        file_content = file.read()
        file_hash = calculate_file_hash(file_content)
        print(f"File hash calculated: {file_hash}")
        
        # Check for duplicate files in database
        user_id = 1  # currently for debugging only
        if Track.check_duplicate_by_hash(user_id, file_hash):
            flash('File already exists! This GPX file has been uploaded before.')
            return redirect(request.url)
        
        # Use default processing parameters for simplified UX
        use_iqr = True  # Default: enable IQR outlier detection
        window_size = 2  # Default: adjacent points
        interpolation_method = 'linear'  # Default: linear interpolation
        
        print(f"Using default processing: IQR={use_iqr}, Window={window_size}, Interpolation={interpolation_method}")
        
        try:
            # Process GPX file with new processor
            processor = GPXProcessor()
            
            # Step 1: Parse GPX content using new three-field structure
            gpx_content = file_content.decode('utf-8')
            parse_result = processor.parse_gpx(gpx_content)
            
            print(f"Debug: Parse result keys: {list(parse_result.keys())}")
            print(f"Debug: Waypoints count: {len(parse_result.get('jsonb_waypoints', []))}")
            print(f"Debug: Metadata: {parse_result.get('jsonb_metadata', {})}")
            
            # Step 2: Apply processing methods
            waypoints = parse_result['jsonb_waypoints']
            processed_statistics = processor.process_with_methods(
                waypoints=waypoints,
                use_iqr=use_iqr,
                window_size=window_size,
                interpolation_method=interpolation_method
            )
            print(f"Debug: processed_statistics = {processed_statistics}")
            
            # Step 3: Prepare final data structure (no converter needed)
            final_data = {
                'jsonb_waypoints': parse_result['jsonb_waypoints'],
                'jsonb_metadata': parse_result['jsonb_metadata'],
                'jsonb_statistics': processed_statistics  # Enhanced statistics with processing results
            }
            
            # Step 4: Validate the complete data structure
            try:
                validate_complete_gpx_data(
                    final_data['jsonb_waypoints'],
                    final_data['jsonb_metadata'],
                    final_data['jsonb_statistics']
                )
                print("Data validation passed successfully")
            except Exception as validation_error:
                print(f"Data validation warning: {validation_error}")
                # Continue processing even if validation has minor issues
            
            # Step 5: Create track record in database using new three-field structure
            track_name = os.path.splitext(filename)[0]  # use filename without extension
            
            track_id = Track.create_with_gpx_data(
                user_id=user_id,
                track_name=track_name,
                gpx_file_content=file_content,  # Store file content directly
                file_hash=file_hash,
                jsonb_waypoints=final_data['jsonb_waypoints'],
                jsonb_metadata=final_data['jsonb_metadata'],
                jsonb_statistics=final_data['jsonb_statistics']
            )
            
            flash(f'File uploaded and processed successfully! Track ID: {track_id} (Default processing applied: IQR outlier detection enabled)')
            
            # Redirect to upload success page with track_id for user choice
            return redirect(url_for('upload_success', track_id=track_id))
            
        except Exception as e:
            flash(f'Error processing GPX file: {str(e)}')
            print(f"Processing error details: {e}")
            return redirect(request.url)
        
    except Exception as e:
        flash(f'Error reading file: {str(e)}')
        print(f"File reading error details: {e}")
        return redirect(request.url)


@app.route('/upload_success/<int:track_id>')
def upload_success(track_id):
    """Show upload success page with options to view results or adjust parameters"""
    track = Track.get_by_id(track_id)
    if not track:
        flash('Track not found')
        return redirect(url_for('dashboard'))
    
    # Extract data from new three-field structure
    waypoints = track.get('jsonb_waypoints', [])
    metadata = track.get('jsonb_metadata', {})
    statistics = track.get('jsonb_statistics', {})
    
    # Get processing results from statistics
    basic_metrics = statistics.get('basic_metrics', {})
    results = statistics.get('results', {})
    processing_methods = statistics.get('processing_methods', {})
    
    print(f"Debug: basic_metrics keys: {list(basic_metrics.keys())}")
    
    # Prepare processing summary for template
    processing_summary = {
        'track_name': track.get('track_name', 'Unknown'),
        'total_distance': basic_metrics.get('total_distance', 0),
        'total_duration': basic_metrics.get('total_duration', '00:00:00'),
        'avg_speed': basic_metrics.get('avg_speed', 0),
        'max_speed': results.get('processed_max_speed', results.get('raw_max_speed', 0)),
        'raw_max_speed': results.get('raw_max_speed', 0),
        'processed_max_speed': results.get('processed_max_speed', 0),
        'outliers_detected': results.get('outliers_detected', 0),
        'outliers_interpolated': results.get('outliers_interpolated', 0),
        'data_points_remaining': results.get('data_points_remaining', 0),
        'waypoint_count': len(waypoints),
        'metadata_waypoint_count': metadata.get('waypoint_count', 0),
        'creator': metadata.get('creator', 'Unknown'),
        'processing_methods_used': {
            'iqr_outlier': processing_methods.get('IQR_Outlier', False),
            'moving_average': processing_methods.get('Moving_Average', False),
            'window_size': processing_methods.get('Window_Size', 2),
            'interpolation_method': processing_methods.get('Interpolation_Method', 'linear')
        }
    }
    
    return render_template('upload_success.html', 
                         track_id=track_id, 
                         processing_summary=processing_summary)