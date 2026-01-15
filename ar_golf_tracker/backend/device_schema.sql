-- Device tracking schema for cross-device sync
-- Tracks devices associated with user accounts and device-specific preferences

-- Devices table
CREATE TABLE IF NOT EXISTS user_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id TEXT NOT NULL,  -- Unique device identifier (e.g., device UUID, IMEI)
    device_type TEXT NOT NULL,  -- 'AR_GLASSES', 'MOBILE_IOS', 'MOBILE_ANDROID', 'WEB'
    device_name TEXT,  -- User-friendly device name (e.g., "John's iPhone")
    
    -- Device-specific preferences (overrides user preferences)
    device_preferences JSONB DEFAULT '{}'::jsonb,
    
    -- Device metadata
    last_sync_at TIMESTAMP,
    last_active_at TIMESTAMP NOT NULL DEFAULT NOW(),
    device_info JSONB,  -- OS version, app version, hardware info, etc.
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_user_device UNIQUE (user_id, device_id)
);

-- Device sync log table (tracks what data has been synced to each device)
CREATE TABLE IF NOT EXISTS device_sync_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES user_devices(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,  -- 'round', 'shot'
    entity_id UUID NOT NULL,
    sync_direction TEXT NOT NULL,  -- 'TO_CLOUD', 'FROM_CLOUD'
    synced_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_device_entity_sync UNIQUE (device_id, entity_type, entity_id, sync_direction)
);

-- Indexes for device tracking
CREATE INDEX IF NOT EXISTS idx_user_devices_user_id ON user_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_user_devices_device_id ON user_devices(device_id);
CREATE INDEX IF NOT EXISTS idx_user_devices_last_active ON user_devices(last_active_at DESC);
CREATE INDEX IF NOT EXISTS idx_device_sync_log_device_id ON device_sync_log(device_id);
CREATE INDEX IF NOT EXISTS idx_device_sync_log_entity ON device_sync_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_device_sync_log_synced_at ON device_sync_log(synced_at DESC);

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_user_devices_updated_at
    BEFORE UPDATE ON user_devices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Helper function to register or update a device
CREATE OR REPLACE FUNCTION register_device(
    p_user_id UUID,
    p_device_id TEXT,
    p_device_type TEXT,
    p_device_name TEXT DEFAULT NULL,
    p_device_info JSONB DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_device_uuid UUID;
BEGIN
    -- Insert or update device
    INSERT INTO user_devices (user_id, device_id, device_type, device_name, device_info, last_active_at)
    VALUES (p_user_id, p_device_id, p_device_type, p_device_name, p_device_info, NOW())
    ON CONFLICT (user_id, device_id)
    DO UPDATE SET
        device_name = COALESCE(EXCLUDED.device_name, user_devices.device_name),
        device_info = COALESCE(EXCLUDED.device_info, user_devices.device_info),
        last_active_at = NOW(),
        is_active = true
    RETURNING id INTO v_device_uuid;
    
    RETURN v_device_uuid;
END;
$$ LANGUAGE plpgsql;

-- Helper function to get user's active devices
CREATE OR REPLACE FUNCTION get_user_devices(
    p_user_id UUID
)
RETURNS TABLE (
    device_uuid UUID,
    device_id TEXT,
    device_type TEXT,
    device_name TEXT,
    last_sync_at TIMESTAMP,
    last_active_at TIMESTAMP,
    device_preferences JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        id,
        user_devices.device_id,
        user_devices.device_type,
        user_devices.device_name,
        user_devices.last_sync_at,
        user_devices.last_active_at,
        user_devices.device_preferences
    FROM user_devices
    WHERE user_id = p_user_id
    AND is_active = true
    ORDER BY last_active_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Helper function to update device sync timestamp
CREATE OR REPLACE FUNCTION update_device_sync_timestamp(
    p_device_uuid UUID
)
RETURNS VOID AS $$
BEGIN
    UPDATE user_devices
    SET last_sync_at = NOW(), last_active_at = NOW()
    WHERE id = p_device_uuid;
END;
$$ LANGUAGE plpgsql;

-- Helper function to log device sync
CREATE OR REPLACE FUNCTION log_device_sync(
    p_device_uuid UUID,
    p_entity_type TEXT,
    p_entity_id UUID,
    p_sync_direction TEXT
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO device_sync_log (device_id, entity_type, entity_id, sync_direction)
    VALUES (p_device_uuid, p_entity_type, p_entity_id, p_sync_direction)
    ON CONFLICT (device_id, entity_type, entity_id, sync_direction)
    DO UPDATE SET synced_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Helper function to get entities that need to be synced to a device
CREATE OR REPLACE FUNCTION get_entities_to_sync(
    p_device_uuid UUID,
    p_user_id UUID,
    p_entity_type TEXT,
    p_since TIMESTAMP DEFAULT NULL
)
RETURNS TABLE (
    entity_id UUID,
    updated_at TIMESTAMP
) AS $$
BEGIN
    IF p_entity_type = 'round' THEN
        RETURN QUERY
        SELECT r.id, r.updated_at
        FROM user_rounds r
        LEFT JOIN device_sync_log dsl ON (
            dsl.device_id = p_device_uuid
            AND dsl.entity_type = 'round'
            AND dsl.entity_id = r.id
            AND dsl.sync_direction = 'FROM_CLOUD'
        )
        WHERE r.user_id = p_user_id
        AND (dsl.synced_at IS NULL OR r.updated_at > dsl.synced_at)
        AND (p_since IS NULL OR r.updated_at > p_since)
        ORDER BY r.updated_at DESC;
    ELSIF p_entity_type = 'shot' THEN
        RETURN QUERY
        SELECT s.id, s.updated_at
        FROM user_shots s
        JOIN user_rounds r ON s.round_id = r.id
        LEFT JOIN device_sync_log dsl ON (
            dsl.device_id = p_device_uuid
            AND dsl.entity_type = 'shot'
            AND dsl.entity_id = s.id
            AND dsl.sync_direction = 'FROM_CLOUD'
        )
        WHERE r.user_id = p_user_id
        AND (dsl.synced_at IS NULL OR s.updated_at > dsl.synced_at)
        AND (p_since IS NULL OR s.updated_at > p_since)
        ORDER BY s.updated_at DESC;
    END IF;
END;
$$ LANGUAGE plpgsql;
