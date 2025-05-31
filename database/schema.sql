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
