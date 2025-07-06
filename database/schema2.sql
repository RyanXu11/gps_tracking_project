-- GPS Tracking Database Schema
-- CST8276 Database Team Project - Group 2
-- Create database user for the team (run as postgres superuser)
CREATE USER dbgroup2 WITH PASSWORD 'cst8276';
ALTER USER dbgroup2 CREATEDB;

-- Create database with team user as owner
DROP DATABASE IF EXISTS gps_tracking_db;

CREATE DATABASE gps_tracking_db
   WITH 
   OWNER = dbgroup2
   ENCODING = 'UTF8';

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE gps_tracking_db TO dbgroup2;

-- Verify database creation
SELECT datname FROM pg_database WHERE datistemplate = false;

-- If running in psql, connect to gps_tracking_db:
\c gps_tracking_db;

-- In DBeaver or other tools, manually select gps_tracking_db before running the following commands.

-------
DROP TABLE if exists tracks;
DROP TABLE if exists users;

-- use hash in password and file name
CREATE EXTENSION IF NOT EXISTS pgcrypto;

select * from tracks;

-- Create users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create tracks table with consolidated statistics
CREATE TABLE tracks (
    track_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    track_name VARCHAR(200) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    
    -- Raw and processed data storage
    gpx_file BYTEA,                    -- Storing raw GPX files
    file_hash VARCHAR(32),             -- Hash to avoid uploading the same file

    -- jsonb formatted data into three fields
    jsonb_waypoints JSONB,             -- Structured data after GPX parsing
    jsonb_metadata JSONB,              -- Metadata for the GPX file
    jsonb_statistics JSONB,            -- Consolidated statistics and indicators
    
    -- Timestamp tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. 授权 dbgroup2 对所有表的访问权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dbgroup2;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dbgroup2;

-- 8. 设置默认权限（将来新表也能访问）
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO dbgroup2;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO dbgroup2;

-- Create indexes for better query performance
CREATE INDEX idx_tracks_user_id ON tracks(user_id);
CREATE INDEX idx_tracks_created_at ON tracks(created_at DESC);
CREATE INDEX idx_tracks_file_hash ON tracks(file_hash);

-- Create GIN indexes on JSONB data for efficient querying
CREATE INDEX idx_tracks_jsonb_waypoints ON tracks USING GIN (jsonb_waypoints);
CREATE INDEX idx_tracks_jsonb_metadata ON tracks USING GIN (jsonb_metadata);
CREATE INDEX idx_tracks_jsonb_statistics ON tracks USING GIN (jsonb_statistics);

-- Create specific indexes for commonly queried basic metrics
CREATE INDEX idx_tracks_start_time ON tracks USING BTREE ((jsonb_statistics->'basic_metrics'->>'start_time'));
CREATE INDEX idx_tracks_end_time ON tracks USING BTREE ((jsonb_statistics->'basic_metrics'->>'end_time'));
CREATE INDEX idx_tracks_total_distance ON tracks USING BTREE (((jsonb_statistics->'basic_metrics'->>'total_distance')::DECIMAL));
CREATE INDEX idx_tracks_total_duration ON tracks USING BTREE ((jsonb_statistics->'basic_metrics'->>'total_duration'));
CREATE INDEX idx_tracks_avg_speed ON tracks USING BTREE (((jsonb_statistics->'basic_metrics'->>'avg_speed')::DECIMAL));

-- Create indexes for processing results
CREATE INDEX idx_tracks_raw_max_speed ON tracks USING BTREE (((jsonb_statistics->'results'->>'raw_max_speed')::DECIMAL));
CREATE INDEX idx_tracks_processed_max_speed ON tracks USING BTREE (((jsonb_statistics->'results'->>'processed_max_speed')::DECIMAL));
CREATE INDEX idx_tracks_outliers_detected ON tracks USING BTREE (((jsonb_statistics->'results'->>'outliers_detected')::INTEGER));

-- Create indexes for processing methods queries
CREATE INDEX idx_tracks_processing_methods ON tracks USING GIN ((jsonb_statistics->'processing_methods'));
CREATE INDEX idx_tracks_iqr_outlier ON tracks USING BTREE (((jsonb_statistics->'processing_methods'->>'IQR_Outlier')::BOOLEAN));

-- Create indexes for metadata queries
CREATE INDEX idx_tracks_creator ON tracks USING BTREE ((jsonb_metadata->>'creator'));
CREATE INDEX idx_tracks_waypoint_count ON tracks USING BTREE (((jsonb_metadata->>'waypoint_count')::INTEGER));

-- Create spatial index for geographic queries (if needed)
-- Note: This would require extracting lat/lng from waypoints into a geometry column for PostGIS
-- CREATE INDEX idx_tracks_spatial ON tracks USING GIST (waypoint_geometry);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_tracks_updated_at 
    BEFORE UPDATE ON tracks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Example of jsonb_statistics structure:
-- {
--   "basic_metrics": {
--     "start_time": "2024-06-04T08:00:00Z",
--     "end_time": "2024-06-04T09:30:00Z",
--     "total_distance": 15.25,
--     "total_duration": "01:30:00",
--     "avg_speed": 10.17
--   },
--   "processing_methods": {
--     "IQR_Outlier": true,
--     "Moving_Average": true
--   },
--   "results": {
--     "raw_max_speed": 695.2,
--     "processed_max_speed": 45.2,
--     "outliers_removed": 8,
--     "data_points_remaining": 485
--   },
--   "optional_metrics": {
--     "elevation_gain": 250.5,
--     "elevation_loss": 180.3,
--      ...
--   },
--   "processing_timestamp": "2024-06-04T10:30:00Z"
-- }

-- Example queries for accessing statistics:

-- Query tracks by distance range (using basic_metrics)
-- SELECT * FROM tracks 
-- WHERE (jsonb_statistics->'basic_metrics'->>'total_distance')::DECIMAL BETWEEN 10.0 AND 20.0;

-- Query tracks by date range (using basic_metrics)
-- SELECT * FROM tracks 
-- WHERE (jsonb_statistics->'basic_metrics'->>'start_time')::TIMESTAMP >= '2024-06-01'
-- AND (jsonb_statistics->'basic_metrics'->>'start_time')::TIMESTAMP <= '2024-06-30';

-- Query tracks that used specific processing methods
-- SELECT * FROM tracks 
-- WHERE (jsonb_statistics->'processing_methods'->>'IQR_Outlier')::BOOLEAN = true;

-- Find tracks with high outlier detection
-- SELECT * FROM tracks 
-- WHERE (jsonb_statistics->'results'->>'outliers_removed')::INTEGER > 5;

-- Compare raw vs processed max speeds
-- SELECT track_name,
--        (jsonb_statistics->'results'->>'raw_max_speed')::DECIMAL as raw_speed,
--        (jsonb_statistics->'results'->>'processed_max_speed')::DECIMAL as processed_speed
-- FROM tracks;

-- Update processing methods (example)
-- UPDATE tracks 
-- SET jsonb_statistics = jsonb_set(
--     jsonb_statistics, 
--     '{processing_methods}', 
--     '{"IQR_Outlier": true, "Moving_Average": true}'::jsonb
-- )
-- WHERE track_id = 1;

INSERT INTO users (username, email, password_hash) VALUES
('carrie', 'wang0974@algonquinlive.com', crypt('cst8319G2', gen_salt('bf'))),
('hongxiu', 'guo00135@algonquinlive.com', crypt('cst8319G2', gen_salt('bf'))),
('lynn', 'xu000146@algonquinlive.com', crypt('cst8319G2', gen_salt('bf'))),
('rachel', 'zu000001@algonquinlive.com', crypt('cst8319G2', gen_salt('bf'))),
('ryan', 'xu000310@algonquinlive.com', crypt('cst8319G2', gen_salt('bf'))),
('yuyang', 'du000084@algonquinlive.com', crypt('cst8319G2', gen_salt('bf')))
ON CONFLICT (username) DO NOTHING;


-- Insert test tracks
INSERT INTO tracks (
    user_id, 
    track_name, 
    description, 
    is_public,
    file_hash,
    jsonb_waypoints,
    jsonb_metadata,
    jsonb_statistics
) VALUES 
(
    1,
    'Morning Bike Ride - Rideau Canal',
    'Beautiful cycling route along the Rideau Canal in Ottawa',
    true,
    'a1b2c3d4e5f6789012345678',
    '[
        {"lat": 45.4215, "lon": -75.6972, "timestamp": "2024-06-04T08:00:00Z", "elevation": 70},
        {"lat": 45.4225, "lon": -75.6962, "timestamp": "2024-06-04T08:02:00Z", "elevation": 72},
        {"lat": 45.4235, "lon": -75.6952, "timestamp": "2024-06-04T08:04:00Z", "elevation": 74},
        {"lat": 45.4245, "lon": -75.6942, "timestamp": "2024-06-04T08:06:00Z", "elevation": 76}
    ]',
    '{
        "waypoint_count": 4,
        "creator": "Garmin Edge 830",
        "version": "1.1",
        "name": "Morning Bike Ride - Rideau Canal",
        "description": "Beautiful cycling route along the Rideau Canal in Ottawa",
        "track_count": 1,
        "route_count": 0,
        "device": "Garmin Edge 830",
        "software": "Garmin Connect",
        "accuracy": "3m"
    }',
    '{
        "basic_metrics": {
            "start_time": "2024-06-04T08:00:00Z",
            "end_time": "2024-06-04T08:45:00Z",
            "total_distance": 12.5,
            "total_duration": "00:45:00",
            "avg_speed": 16.7
        },
        "processing_methods": {
            "IQR_Outlier": true,
            "Moving_Average": true,
            "Window_Size": 3,
            "Interpolation_Method": "linear"
        },
        "results": {
            "raw_max_speed": 65.4,
            "processed_max_speed": 52.3,
            "outliers_detected": 3,
            "outliers_interpolated": 3,
            "data_points_remaining": 267
        },
        "optional_metrics": {
            "elevation_gain": 45.2,
            "elevation_loss": 38.7,
            "calories_burned": 420
        }
    }'
),
(
    2,
    'Evening Jog - Experimental Farm',
    'Running through Central Experimental Farm with GPS signal issues',
    false,
    'f9e8d7c6b5a4321098765432',
    '[
        {"lat": 45.3833, "lon": -75.7089, "timestamp": "2024-06-03T19:00:00Z", "elevation": 85},
        {"lat": 45.3843, "lon": -75.7079, "timestamp": "2024-06-03T19:03:00Z", "elevation": 87},
        {"lat": 45.3853, "lon": -75.7069, "timestamp": "2024-06-03T19:06:00Z", "elevation": 89}
    ]',
    '{
        "waypoint_count": 3,
        "creator": "iPhone 14 Pro",
        "version": "1.1", 
        "name": "Evening Jog - Experimental Farm",
        "description": "Running through Central Experimental Farm with GPS signal issues",
        "track_count": 1,
        "route_count": 0,
        "device": "iPhone 14 Pro",
        "software": "Strava App",
        "accuracy": "5m"
    }',
    '{
        "basic_metrics": {
            "start_time": "2024-06-03T19:00:00Z",
            "end_time": "2024-06-03T19:35:00Z",
            "total_distance": 5.8,
            "total_duration": "00:35:00",
            "avg_speed": 9.9
        },
        "processing_methods": {
            "IQR_Outlier": true,
            "Moving_Average": false,
            "Window_Size": 2,
            "Interpolation_Method": "linear"
        },
        "results": {
            "raw_max_speed": 695.2,
            "processed_max_speed": 18.4,
            "outliers_detected": 12,
            "outliers_interpolated": 12,
            "data_points_remaining": 198
        },
        "optional_metrics": {
            "elevation_gain": 28.5,
            "elevation_loss": 32.1,
            "calories_burned": 280,
            "heart_rate": {
                "avg": 155,
                "max": 172,
                "min": 120
            }
        }
    }'
);

-- Verify the inserted data
-- Comprehensive verification of tracks data with new structure
SELECT 
    t.track_id,
    t.track_name,
    u.username,
    t.is_public,
    
    -- Basic Metrics
    t.jsonb_statistics->'basic_metrics'->>'start_time' as start_time,
    t.jsonb_statistics->'basic_metrics'->>'end_time' as end_time,
    t.jsonb_statistics->'basic_metrics'->>'total_distance' as distance_km,
    t.jsonb_statistics->'basic_metrics'->>'total_duration' as duration,
    t.jsonb_statistics->'basic_metrics'->>'avg_speed' as avg_speed_kmh,
    
    -- Processing Results
    t.jsonb_statistics->'results'->>'raw_max_speed' as raw_max_speed,
    t.jsonb_statistics->'results'->>'processed_max_speed' as processed_max_speed,
    t.jsonb_statistics->'results'->>'outliers_detected' as outliers_detected,
    t.jsonb_statistics->'results'->>'data_points_remaining' as data_points_remaining,
    
    -- Processing Methods
    t.jsonb_statistics->'processing_methods'->>'IQR_Outlier' as used_iqr,
    t.jsonb_statistics->'processing_methods'->>'Moving_Average' as used_moving_avg,
    t.jsonb_statistics->'processing_methods'->>'Window_Size' as window_size,
    t.jsonb_statistics->'processing_methods'->>'Interpolation_Method' as interpolation_method,
    
    -- Metadata Information
    t.jsonb_metadata->>'waypoint_count' as waypoint_count,
    t.jsonb_metadata->>'creator' as device_creator,
    t.jsonb_metadata->>'software' as recording_software,
    t.jsonb_metadata->>'accuracy' as gps_accuracy,
    
    -- Waypoints Data Summary
    jsonb_array_length(t.jsonb_waypoints) as actual_waypoint_count,
    t.jsonb_waypoints->0->>'lat' as first_lat,
    t.jsonb_waypoints->0->>'lon' as first_lon,
    t.jsonb_waypoints->(jsonb_array_length(t.jsonb_waypoints)-1)->>'lat' as last_lat,
    t.jsonb_waypoints->(jsonb_array_length(t.jsonb_waypoints)-1)->>'lon' as last_lon,
    
    -- File Information
    t.file_hash,
    length(t.gpx_file) as gpx_file_size_bytes,
    
    -- Timestamps
    t.created_at,
    t.updated_at
    
FROM tracks t
JOIN users u ON t.user_id = u.user_id
ORDER BY t.created_at DESC;

-- Additional verification queries for data integrity

-- Check for data consistency between metadata and actual waypoints
SELECT 
    track_id,
    track_name,
    (jsonb_metadata->>'waypoint_count')::INTEGER as metadata_count,
    jsonb_array_length(jsonb_waypoints) as actual_count,
    CASE 
        WHEN (jsonb_metadata->>'waypoint_count')::INTEGER = jsonb_array_length(jsonb_waypoints) 
        THEN '✓ Match' 
        ELSE '✗ Mismatch' 
    END as count_status
FROM tracks
ORDER BY track_id;

-- Summary statistics across all tracks
SELECT 
    COUNT(*) as total_tracks,
    COUNT(DISTINCT user_id) as unique_users,
    AVG((jsonb_statistics->'basic_metrics'->>'total_distance')::DECIMAL) as avg_distance_km,
    MAX((jsonb_statistics->'basic_metrics'->>'total_distance')::DECIMAL) as max_distance_km,
    MIN((jsonb_statistics->'basic_metrics'->>'total_distance')::DECIMAL) as min_distance_km,
    AVG((jsonb_statistics->'basic_metrics'->>'avg_speed')::DECIMAL) as avg_speed_across_tracks,
    COUNT(CASE WHEN (jsonb_statistics->'processing_methods'->>'IQR_Outlier')::BOOLEAN = true THEN 1 END) as tracks_with_iqr,
    COUNT(CASE WHEN (jsonb_statistics->'processing_methods'->>'Moving_Average')::BOOLEAN = true THEN 1 END) as tracks_with_moving_avg
FROM tracks;

-- Check JSON structure integrity
SELECT 
    track_id,
    track_name,
    CASE 
        WHEN jsonb_typeof(jsonb_waypoints) = 'array' THEN '✓ Array' 
        ELSE '✗ Not Array' 
    END as waypoints_structure,
    CASE 
        WHEN jsonb_typeof(jsonb_metadata) = 'object' THEN '✓ Object' 
        ELSE '✗ Not Object' 
    END as metadata_structure,
    CASE 
        WHEN jsonb_typeof(jsonb_statistics) = 'object' THEN '✓ Object' 
        ELSE '✗ Not Object' 
    END as statistics_structure,
    CASE 
        WHEN jsonb_statistics ? 'basic_metrics' AND 
             jsonb_statistics ? 'processing_methods' AND 
             jsonb_statistics ? 'results' THEN '✓ Complete' 
        ELSE '✗ Missing Keys' 
    END as statistics_completeness
FROM tracks
ORDER BY track_id;