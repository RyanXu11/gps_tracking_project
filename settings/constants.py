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
    # User queries
    'GET_USER_BY_ID': "SELECT * FROM users WHERE user_id = %s",
    'GET_USER_BY_USERNAME': "SELECT * FROM users WHERE username = %s",
    
    # Basic track queries
    'GET_TRACKS_BY_TRACK': "SELECT * FROM tracks WHERE track_id = %s",
    'GET_TRACKS_BY_USER': "SELECT * FROM tracks WHERE user_id = %s ORDER BY created_at DESC",
    
    # Duplicate check
    'CHECK_DUPLICATE_HASH': "SELECT COUNT(*) as count FROM tracks WHERE user_id = %s AND file_hash = %s",
    
    # Track creation - Updated for new three-field structure
    'CREATE_BASIC_TRACK': """
        INSERT INTO tracks (user_id, track_name, description, is_public) 
        VALUES (%s, %s, %s, %s) RETURNING track_id
    """,
    'CREATE_FULL_TRACK': """
        INSERT INTO tracks (
            user_id, track_name, description, is_public, 
            gpx_file, file_hash, jsonb_waypoints, jsonb_metadata, jsonb_statistics
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING track_id
    """,
    
    # Track updates
    'UPDATE_TRACK_STATISTICS': """
        UPDATE tracks SET 
            jsonb_statistics = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE track_id = %s
    """,
    'UPDATE_TRACK_VISIBILITY': """
        UPDATE tracks SET 
            is_public = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE track_id = %s
    """,
    
    # Advanced queries using new JSONB structure
    'GET_TRACKS_BY_PROCESSING_METHOD': """
        SELECT * FROM tracks 
        WHERE user_id = %s 
        AND (jsonb_statistics->'processing_methods'->>%s)::BOOLEAN = %s
        ORDER BY created_at DESC
    """,
    'GET_TRACKS_BY_DISTANCE_RANGE': """
        SELECT * FROM tracks 
        WHERE user_id = %s 
        AND (jsonb_statistics->'basic_metrics'->>'total_distance')::DECIMAL BETWEEN %s AND %s
        ORDER BY created_at DESC
    """,
    'GET_TRACKS_BY_DATE_RANGE': """
        SELECT * FROM tracks 
        WHERE user_id = %s 
        AND (jsonb_statistics->'basic_metrics'->>'start_time')::TIMESTAMP BETWEEN %s AND %s
        ORDER BY created_at DESC
    """,
    'GET_TRACKS_BY_MAX_SPEED': """
        SELECT * FROM tracks 
        WHERE user_id = %s 
        AND (jsonb_statistics->'results'->>'processed_max_speed')::DECIMAL <= %s
        ORDER BY created_at DESC
    """,
    
    # New queries for accessing individual JSONB fields
    'GET_TRACK_WAYPOINTS_SUMMARY': """
        SELECT 
            track_id,
            track_name,
            jsonb_array_length(jsonb_waypoints) as waypoint_count,
            jsonb_waypoints->0->>'lat' as first_lat,
            jsonb_waypoints->0->>'lon' as first_lon,
            jsonb_waypoints->(jsonb_array_length(jsonb_waypoints)-1)->>'lat' as last_lat,
            jsonb_waypoints->(jsonb_array_length(jsonb_waypoints)-1)->>'lon' as last_lon,
            (SELECT json_agg(wp) FROM (
                SELECT * FROM jsonb_array_elements(jsonb_waypoints) wp LIMIT %s
            ) sub) as sample_waypoints
        FROM tracks 
        WHERE track_id = %s
    """,
    'GET_TRACK_METADATA': """
        SELECT jsonb_metadata FROM tracks WHERE track_id = %s
    """,
    'GET_TRACK_STATISTICS': """
        SELECT jsonb_statistics FROM tracks WHERE track_id = %s
    """,
    
    # Public tracks queries - Updated for new structure
    'GET_PUBLIC_TRACKS': """
        SELECT t.*, u.username FROM tracks t
        JOIN users u ON t.user_id = u.user_id
        WHERE t.is_public = true
        ORDER BY t.created_at DESC
        LIMIT %s OFFSET %s
    """,
    'GET_PUBLIC_TRACKS_BY_DISTANCE': """
        SELECT t.*, u.username FROM tracks t
        JOIN users u ON t.user_id = u.user_id
        WHERE t.is_public = true
        AND (t.jsonb_statistics->'basic_metrics'->>'total_distance')::DECIMAL BETWEEN %s AND %s
        ORDER BY t.created_at DESC
    """,
    
    # Statistics queries - Updated for new structure
    'GET_USER_TRACK_STATS': """
        SELECT 
            COUNT(*) as total_tracks,
            AVG((jsonb_statistics->'basic_metrics'->>'total_distance')::DECIMAL) as avg_distance,
            MAX((jsonb_statistics->'basic_metrics'->>'total_distance')::DECIMAL) as max_distance,
            SUM((jsonb_statistics->'basic_metrics'->>'total_distance')::DECIMAL) as total_distance,
            AVG((jsonb_statistics->'basic_metrics'->>'avg_speed')::DECIMAL) as avg_speed_overall,
            MAX((jsonb_statistics->'results'->>'processed_max_speed')::DECIMAL) as max_speed_overall
        FROM tracks 
        WHERE user_id = %s
    """,
    'GET_PROCESSING_METHOD_USAGE': """
        SELECT 
            COUNT(CASE WHEN (jsonb_statistics->'processing_methods'->>'IQR_Outlier')::BOOLEAN = true THEN 1 END) as iqr_usage,
            COUNT(CASE WHEN (jsonb_statistics->'processing_methods'->>'Moving_Average')::BOOLEAN = true THEN 1 END) as ma_usage,
            COUNT(*) as total_tracks,
            ROUND(AVG((jsonb_statistics->'results'->>'outliers_detected')::INTEGER), 2) as avg_outliers_detected,
            ROUND(AVG((jsonb_statistics->'results'->>'data_points_remaining')::INTEGER), 2) as avg_data_points_remaining
        FROM tracks 
        WHERE user_id = %s
    """,
    
    # Advanced analysis queries using new structure
    'GET_TRACKS_WITH_METADATA_INFO': """
        SELECT 
            track_id,
            track_name,
            jsonb_metadata->>'creator' as device_creator,
            jsonb_metadata->>'software' as recording_software,
            jsonb_metadata->>'waypoint_count' as metadata_waypoint_count,
            jsonb_array_length(jsonb_waypoints) as actual_waypoint_count,
            jsonb_statistics->'basic_metrics'->>'total_distance' as distance,
            created_at
        FROM tracks 
        WHERE user_id = %s
        ORDER BY created_at DESC
    """,
    'GET_TRACKS_BY_DEVICE': """
        SELECT * FROM tracks 
        WHERE user_id = %s 
        AND jsonb_metadata->>'creator' ILIKE %s
        ORDER BY created_at DESC
    """,
    'GET_WAYPOINT_DENSITY_ANALYSIS': """
        SELECT 
            track_id,
            track_name,
            jsonb_array_length(jsonb_waypoints) as waypoint_count,
            (jsonb_statistics->'basic_metrics'->>'total_distance')::DECIMAL as distance_km,
            ROUND(
                jsonb_array_length(jsonb_waypoints) / 
                NULLIF((jsonb_statistics->'basic_metrics'->>'total_distance')::DECIMAL, 0), 
                2
            ) as waypoints_per_km
        FROM tracks 
        WHERE user_id = %s
        AND jsonb_statistics->'basic_metrics'->>'total_distance' IS NOT NULL
        ORDER BY waypoints_per_km DESC NULLS LAST
    """,
    
    # Data quality queries
    'GET_TRACKS_WITH_DATA_QUALITY_ISSUES': """
        SELECT 
            track_id,
            track_name,
            (jsonb_statistics->'results'->>'outliers_detected')::INTEGER as outliers_detected,
            (jsonb_statistics->'results'->>'raw_max_speed')::DECIMAL as raw_max_speed,
            (jsonb_statistics->'results'->>'processed_max_speed')::DECIMAL as processed_max_speed,
            CASE 
                WHEN (jsonb_statistics->'results'->>'outliers_detected')::INTEGER > 10 THEN 'High outliers'
                WHEN (jsonb_statistics->'results'->>'raw_max_speed')::DECIMAL > 200 THEN 'Unrealistic speed'
                ELSE 'Good quality'
            END as quality_assessment
        FROM tracks 
        WHERE user_id = %s
        ORDER BY (jsonb_statistics->'results'->>'outliers_detected')::INTEGER DESC
    """,
    
    # Track deletion
    'DELETE_TRACK': "DELETE FROM tracks WHERE track_id = %s AND user_id = %s"
}