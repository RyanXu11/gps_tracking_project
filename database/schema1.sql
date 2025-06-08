-- GPS Tracking Database Schema
-- CST8276 Database Team Project - Group 2

-- Create database user for the team (run as postgres superuser)
--CREATE USER dbgroup2 WITH PASSWORD 'cst8276';
--ALTER USER dbgroup2 CREATEDB;

-- Create database with team user as owner
--DROP DATABASE IF EXISTS gps_tracking_db;

--CREATE DATABASE gps_tracking_db
--    WITH 
--    OWNER = dbgroup2
--    ENCODING = 'UTF8';

-- Grant necessary permissions
--GRANT ALL PRIVILEGES ON DATABASE gps_tracking_db TO dbgroup2;

-- Verify database creation
--SELECT datname FROM pg_database WHERE datistemplate = false;

-- Connect to gps_tracking_db in PostgreSQL, or create new connection in DBeaver
--\c gps_tracking_db;

DROP TABLE if exists users;
DROP TABLE if exists tracks;

-- Create users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tracks table
CREATE TABLE tracks (
    track_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    track_name VARCHAR(200) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    
    -- Raw and processed data storage
    gpx_file BYTEA,           -- Storing raw GPX files
    jsonb_track_data JSONB,         -- Structured data after GPX parsing
    
    -- Extracted key indicators for quick querying
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_distance DECIMAL(10,2),    -- km
    total_duration INTERVAL,         -- Duration
    max_speed DECIMAL(5,2),          -- km/h
    avg_speed DECIMAL(5,2),          -- km/h
    
    -- Timestamp tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_tracks_user_id ON tracks(user_id);
CREATE INDEX idx_tracks_start_time ON tracks(start_time);
CREATE INDEX idx_tracks_created_at ON tracks(created_at DESC);
CREATE INDEX idx_tracks_distance ON tracks(total_distance);

-- Create index on JSONB data for geographic queries
CREATE INDEX idx_tracks_jsonb_waypoints ON tracks USING GIN ((jsonb_track_data->'waypoints'));

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

--------------------------------------------------------------------
-- Sample data for GPS Tracking Database
-- Insert team members as users

-- Ensure pgcrypto extension used for hash password
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Insert test users, the initial password is "cst8319G2"
INSERT INTO users (username, email, password_hash) VALUES
('carrie', 'wang0974@algonquinlive.com', crypt('cst8319G2', gen_salt('bf'))),
('hongxiu', 'guo00135@algonquinlive.com', crypt('cst8319G2', gen_salt('bf'))),
('lynn', 'xu000146@algonquinlive.com', crypt('cst8319G2', gen_salt('bf'))),
('rachel', 'zu000001@algonquinlive.com', crypt('cst8319G2', gen_salt('bf'))),
('ryan', 'xu000310@algonquinlive.com', crypt('cst8319G2', gen_salt('bf'))),
('yuyang', 'du000084@algonquinlive.com', crypt('cst8319G2', gen_salt('bf')))
ON CONFLICT (username) DO NOTHING;

-- Sample track data (not real gpx file, just for initial testing)
INSERT INTO tracks (
    user_id, 
    track_name, 
    description,
    start_time,
    end_time,
    total_distance,
    total_duration,
    max_speed,
    avg_speed,
    jsonb_track_data
) VALUES
(
    1,  -- carrie's user_id
    'Ottawa University Campus Run',
    '5km morning run around campus',
    '2025-05-15 08:00:00',
    '2025-05-15 08:25:00',
    5.2,
    '00:25:00',
    18.5,
    12.5,
    '{"metadata": {"name": "Campus Run", "creator": "Garmin"}, "waypoints": [{"lat": 45.4215, "lon": -75.6972, "ele": 70, "time": "2025-05-15T08:00:00Z"}]}'
),
(
    2,  -- hongxiu's user_id
    'Rideau Canal Bike Ride',
    '15km bike ride along the canal',
    '2025-05-16 14:00:00',
    '2025-05-16 14:45:00',
    15.8,
    '00:45:00',
    35.2,
    21.1,
    '{"metadata": {"name": "Canal Ride", "creator": "Strava"}, "waypoints": [{"lat": 45.4165, "lon": -75.7009, "ele": 65, "time": "2025-05-16T14:00:00Z"}]}'
);


-- Verify data insertion
SELECT 
    u.username,
    t.track_name,
    t.total_distance,
    t.avg_speed,
    t.created_at
FROM users u
JOIN tracks t ON u.user_id = t.user_id
ORDER BY t.created_at DESC;