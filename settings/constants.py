# Database Configuration
DATABASE_URL = "postgresql://dbgroup2:cst8276G2@localhost/gps_tracking_db"

# Flask Configuration
SECRET_KEY = "gps-tracking-secret-key-2025"
DEBUG_MODE = True

# File Upload Configuration
SAMPLE_DATA_BASE = "sample_data"
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'gpx'}

# GPX Processing Configuration
# DEFAULT_BATCH_SIZE = 1000
# MAX_WAYPOINTS_PER_TRACK = 50000
# GPX_NAMESPACE = '{http://www.topografix.com/GPX/1/1}'
TIMEZONE_STR="America/Toronto"

# SQL statements
SQL_QUERIES = {
    'GET_USER_BY_ID': "SELECT * FROM users WHERE user_id = %s",
    'GET_USER_BY_USERNAME': "SELECT * FROM users WHERE username = %s",
    'GET_TRACKS_BY_TRACK': "SELECT * FROM tracks WHERE track_id = %s",
    'GET_TRACKS_BY_USER': "SELECT * FROM tracks WHERE user_id = %s ORDER BY created_at DESC",
    'CHECK_DUPLICATE_HASH': "SELECT COUNT(*) as count FROM tracks WHERE user_id = %s AND file_hash = %s",
    'CREATE_BASIC_TRACK': "INSERT INTO tracks (user_id, track_name, description) VALUES (%s, %s, %s) RETURNING track_id",
    'CREATE_FULL_TRACK': """
        INSERT INTO tracks (
            user_id, track_name, description, gpx_file, jsonb_track_data,
            start_time, end_time, total_distance, total_duration,
            max_speed, avg_speed, file_hash, skip_points
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING track_id
    """,
    'UPDATE_TRACK': """
        UPDATE tracks SET 
            jsonb_track_data = %s,
            max_speed = %s,
            skip_points = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE track_id = %s
    """    
}