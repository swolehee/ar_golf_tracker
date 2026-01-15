-- SQLite schema for AR glasses local storage
-- Stores shot data locally during rounds for offline operation

-- Rounds table
CREATE TABLE IF NOT EXISTS rounds (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT,
    course_name TEXT,
    start_time INTEGER NOT NULL,
    end_time INTEGER,
    weather_temperature REAL,
    weather_wind_speed REAL,
    weather_wind_direction TEXT,
    weather_conditions TEXT,
    sync_status TEXT NOT NULL DEFAULT 'PENDING',
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- Shots table
CREATE TABLE IF NOT EXISTS shots (
    id TEXT PRIMARY KEY,
    round_id TEXT NOT NULL,
    hole_number INTEGER NOT NULL,
    swing_number INTEGER NOT NULL,
    club_type TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    gps_lat REAL NOT NULL,
    gps_lon REAL NOT NULL,
    gps_accuracy REAL NOT NULL,
    gps_altitude REAL,
    gps_timestamp INTEGER NOT NULL,
    distance_value REAL,
    distance_unit TEXT,
    distance_accuracy TEXT,
    notes TEXT,
    sync_status TEXT NOT NULL DEFAULT 'PENDING',
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (round_id) REFERENCES rounds(id) ON DELETE CASCADE
);

-- Sync queue for offline operation
CREATE TABLE IF NOT EXISTS sync_queue (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,  -- 'ROUND', 'SHOT'
    entity_id TEXT NOT NULL,
    operation TEXT NOT NULL,    -- 'CREATE', 'UPDATE', 'DELETE'
    payload TEXT NOT NULL,      -- JSON serialized entity
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_retry_at INTEGER,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_rounds_user_id ON rounds(user_id);
CREATE INDEX IF NOT EXISTS idx_rounds_sync_status ON rounds(sync_status);
CREATE INDEX IF NOT EXISTS idx_rounds_start_time ON rounds(start_time);

CREATE INDEX IF NOT EXISTS idx_shots_round_id ON shots(round_id);
CREATE INDEX IF NOT EXISTS idx_shots_hole_number ON shots(hole_number);
CREATE INDEX IF NOT EXISTS idx_shots_sync_status ON shots(sync_status);
CREATE INDEX IF NOT EXISTS idx_shots_timestamp ON shots(timestamp);

CREATE INDEX IF NOT EXISTS idx_sync_queue_entity ON sync_queue(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_sync_queue_created_at ON sync_queue(created_at);

-- Trigger to update updated_at timestamp on rounds
CREATE TRIGGER IF NOT EXISTS update_rounds_timestamp 
AFTER UPDATE ON rounds
BEGIN
    UPDATE rounds SET updated_at = strftime('%s', 'now') WHERE id = NEW.id;
END;

-- Trigger to update updated_at timestamp on shots
CREATE TRIGGER IF NOT EXISTS update_shots_timestamp 
AFTER UPDATE ON shots
BEGIN
    UPDATE shots SET updated_at = strftime('%s', 'now') WHERE id = NEW.id;
END;

-- Trigger to update updated_at timestamp on sync_queue
CREATE TRIGGER IF NOT EXISTS update_sync_queue_timestamp 
AFTER UPDATE ON sync_queue
BEGIN
    UPDATE sync_queue SET updated_at = strftime('%s', 'now') WHERE id = NEW.id;
END;
