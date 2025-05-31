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