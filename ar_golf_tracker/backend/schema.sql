-- PostgreSQL schema with PostGIS for cloud backend
-- Stores user data, course information, and synchronized shot data

-- Enable PostGIS extension for geographic data
CREATE EXTENSION IF NOT EXISTS postgis;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- User preferences (stored as JSONB for flexibility)
    preferences JSONB DEFAULT '{
        "distance_unit": "YARDS",
        "auto_sync": true,
        "data_retention_days": 730
    }'::jsonb,
    
    -- Calibration data
    calibration_model_key TEXT,  -- S3 key for custom club recognition model
    swing_profile JSONB  -- Swing characteristics for calibration
);

-- Courses table with geographic data
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,  -- Course center point (WGS84)
    address TEXT,
    total_holes INTEGER NOT NULL,
    par INTEGER NOT NULL,
    yardage INTEGER NOT NULL,
    rating REAL,
    slope INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Holes table with geographic features
CREATE TABLE IF NOT EXISTS holes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    hole_number INTEGER NOT NULL,
    par INTEGER NOT NULL,
    yardage INTEGER NOT NULL,
    tee_box_location GEOGRAPHY(POINT, 4326) NOT NULL,
    green_location GEOGRAPHY(POINT, 4326) NOT NULL,
    fairway_polygon GEOGRAPHY(POLYGON, 4326),
    hazards JSONB,  -- Array of hazard objects with type and polygon
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_course_hole UNIQUE (course_id, hole_number)
);

-- User rounds table
CREATE TABLE IF NOT EXISTS user_rounds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    course_name TEXT NOT NULL,  -- Denormalized for when course is deleted
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    weather_conditions JSONB,  -- Weather data during round
    sync_status TEXT NOT NULL DEFAULT 'SYNCED',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- User shots table
CREATE TABLE IF NOT EXISTS user_shots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    round_id UUID NOT NULL REFERENCES user_rounds(id) ON DELETE CASCADE,
    hole_number INTEGER NOT NULL,
    swing_number INTEGER NOT NULL,
    club_type TEXT NOT NULL,
    shot_time TIMESTAMP NOT NULL,
    gps_origin GEOGRAPHY(POINT, 4326) NOT NULL,
    gps_accuracy REAL NOT NULL,  -- meters
    gps_altitude REAL,
    distance_yards REAL,
    distance_accuracy TEXT,  -- 'HIGH', 'MEDIUM', 'LOW'
    notes TEXT,
    sync_status TEXT NOT NULL DEFAULT 'SYNCED',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Sync conflicts table for logging conflict resolution
CREATE TABLE IF NOT EXISTS sync_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,  -- 'round', 'shot'
    entity_id UUID NOT NULL,
    resolution_strategy TEXT NOT NULL,  -- 'last_write_wins', 'manual', etc.
    conflict_data JSONB NOT NULL,  -- Full conflict details
    resolved_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for performance

-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Course indexes
CREATE INDEX IF NOT EXISTS idx_courses_location ON courses USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_courses_name ON courses(name);

-- Hole indexes
CREATE INDEX IF NOT EXISTS idx_holes_course_id ON holes(course_id);
CREATE INDEX IF NOT EXISTS idx_holes_tee_location ON holes USING GIST(tee_box_location);
CREATE INDEX IF NOT EXISTS idx_holes_green_location ON holes USING GIST(green_location);

-- Round indexes
CREATE INDEX IF NOT EXISTS idx_user_rounds_user_id ON user_rounds(user_id);
CREATE INDEX IF NOT EXISTS idx_user_rounds_course_id ON user_rounds(course_id);
CREATE INDEX IF NOT EXISTS idx_user_rounds_start_time ON user_rounds(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_user_rounds_sync_status ON user_rounds(sync_status);

-- Shot indexes
CREATE INDEX IF NOT EXISTS idx_user_shots_round_id ON user_shots(round_id);
CREATE INDEX IF NOT EXISTS idx_user_shots_hole_number ON user_shots(hole_number);
CREATE INDEX IF NOT EXISTS idx_user_shots_club_type ON user_shots(club_type);
CREATE INDEX IF NOT EXISTS idx_user_shots_shot_time ON user_shots(shot_time);
CREATE INDEX IF NOT EXISTS idx_user_shots_gps_origin ON user_shots USING GIST(gps_origin);
CREATE INDEX IF NOT EXISTS idx_user_shots_sync_status ON user_shots(sync_status);

-- Conflict indexes
CREATE INDEX IF NOT EXISTS idx_sync_conflicts_user_id ON sync_conflicts(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_conflicts_entity ON sync_conflicts(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_sync_conflicts_created_at ON sync_conflicts(created_at DESC);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_user_rounds_user_start ON user_rounds(user_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_user_shots_round_hole ON user_shots(round_id, hole_number);

-- Triggers to update updated_at timestamp

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_courses_updated_at
    BEFORE UPDATE ON courses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_holes_updated_at
    BEFORE UPDATE ON holes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_rounds_updated_at
    BEFORE UPDATE ON user_rounds
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_shots_updated_at
    BEFORE UPDATE ON user_shots
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Helper function to find courses near a location
CREATE OR REPLACE FUNCTION find_courses_near_location(
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    radius_meters INTEGER DEFAULT 1000
)
RETURNS TABLE (
    course_id UUID,
    course_name TEXT,
    distance_meters DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.name,
        ST_Distance(c.location, ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography) as distance
    FROM courses c
    WHERE ST_DWithin(
        c.location,
        ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography,
        radius_meters
    )
    ORDER BY distance;
END;
$$ LANGUAGE plpgsql;

-- Helper function to find the current hole based on GPS position
CREATE OR REPLACE FUNCTION find_current_hole(
    p_course_id UUID,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    proximity_meters INTEGER DEFAULT 20
)
RETURNS INTEGER AS $$
DECLARE
    current_hole INTEGER;
BEGIN
    SELECT h.hole_number INTO current_hole
    FROM holes h
    WHERE h.course_id = p_course_id
    AND ST_DWithin(
        h.tee_box_location,
        ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography,
        proximity_meters
    )
    ORDER BY ST_Distance(
        h.tee_box_location,
        ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography
    )
    LIMIT 1;
    
    RETURN current_hole;
END;
$$ LANGUAGE plpgsql;
