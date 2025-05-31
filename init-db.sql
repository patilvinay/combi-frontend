-- Drop existing tables if they exist
DROP TABLE IF EXISTS measurements CASCADE;

-- Single table for all measurements
CREATE TABLE measurements (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    enqueued_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Phase 1
    v1 FLOAT,
    i1 FLOAT,
    p1 FLOAT,
    pf1 FLOAT,
    
    -- Phase 2
    v2 FLOAT,
    i2 FLOAT,
    p2 FLOAT,
    pf2 FLOAT,
    
    -- Phase 3
    v3 FLOAT,
    i3 FLOAT,
    p3 FLOAT,
    pf3 FLOAT,
    
    -- Additional phases if needed
    v4 FLOAT,
    i4 FLOAT,
    p4 FLOAT,
    pf4 FLOAT,
    
    v5 FLOAT,
    i5 FLOAT,
    p5 FLOAT,
    pf5 FLOAT,
    
    v6 FLOAT,
    i6 FLOAT,
    p6 FLOAT,
    pf6 FLOAT,
    
    v7 FLOAT,
    i7 FLOAT,
    p7 FLOAT,
    pf7 FLOAT,
    
    -- Common measurements
    frequency FLOAT
);

-- Indexes for better query performance
CREATE INDEX idx_measurements_device_id ON measurements(device_id);
CREATE INDEX idx_measurements_enqueued_time ON measurements(enqueued_time);

-- Function to insert a new measurement
CREATE OR REPLACE FUNCTION insert_measurement(
    p_device_id VARCHAR,
    p_voltages FLOAT[],
    p_currents FLOAT[],
    p_power FLOAT[],
    p_power_factor FLOAT[],
    p_frequency FLOAT,
    p_enqueued_time TIMESTAMP WITH TIME ZONE
) 
RETURNS INTEGER AS $$
BEGIN
    INSERT INTO measurements (
        device_id,
        enqueued_time,
        
        v1, i1, p1, pf1,
        v2, i2, p2, pf2,
        v3, i3, p3, pf3,
        v4, i4, p4, pf4,
        v5, i5, p5, pf5,
        v6, i6, p6, pf6,
        v7, i7, p7, pf7,
        frequency
    ) VALUES (
        p_device_id,
        p_enqueued_time,
        
        p_voltages[1], p_currents[1], p_power[1], p_power_factor[1],
        p_voltages[2], p_currents[2], p_power[2], p_power_factor[2],
        p_voltages[3], p_currents[3], p_power[3], p_power_factor[3],
        p_voltages[4], p_currents[4], p_power[4], p_power_factor[4],
        p_voltages[5], p_currents[5], p_power[5], p_power_factor[5],
        p_voltages[6], p_currents[6], p_power[6], p_power_factor[6],
        p_voltages[7], p_currents[7], p_power[7], p_power_factor[7],
        p_frequency
    );
    
    RETURN 1;
END;
$$ LANGUAGE plpgsql;

-- Insert sample data for device 1
SELECT insert_measurement(
    '48:CA:43:36:71:04',
    ARRAY[220.1, 219.8, 220.5, 0, 0, 0, 0],
    ARRAY[5.2, 5.1, 5.3, 0, 0, 0, 0],
    ARRAY[1144.5, 1120.9, 1168.6, 0, 0, 0, 0],
    ARRAY[0.99, 0.98, 1.0, 1, 1, 1, 1],
    50.0,
    '2025-05-31 12:00:00+05:30'
);

-- Insert another sample for device 1 (5 minutes later)
SELECT insert_measurement(
    '48:CA:43:36:71:04',
    ARRAY[219.9, 220.2, 220.0, 0, 0, 0, 0],
    ARRAY[5.3, 5.2, 5.4, 0, 0, 0, 0],
    ARRAY[1165.4, 1145.0, 1188.0, 0, 0, 0, 0],
    ARRAY[0.99, 0.99, 1.0, 1, 1, 1, 1],
    50.0,
    '2025-05-31 12:05:00+05:30'
);

-- Insert sample for a different device
SELECT insert_measurement(
    '12:34:56:78:90:AB',
    ARRAY[110.5, 110.2, 110.8, 0, 0, 0, 0],
    ARRAY[2.5, 2.4, 2.6, 0, 0, 0, 0],
    ARRAY[276.2, 264.5, 288.1, 0, 0, 0, 0],
    ARRAY[1.0, 1.0, 1.0, 1, 1, 1, 1],
    60.0,
    '2025-05-31 12:00:00-05:00'
);

-- Create a view for easy querying of the latest measurements
CREATE OR REPLACE VIEW latest_measurements AS
WITH ranked_measurements AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY enqueued_time DESC) as rn
    FROM measurements
)
SELECT 
    id,
    device_id,
    enqueued_time,
    v1, i1, p1, pf1,
    v2, i2, p2, pf2,
    v3, i3, p3, pf3,
    frequency
FROM ranked_measurements
WHERE rn = 1;
