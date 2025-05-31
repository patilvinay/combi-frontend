-- Add frequency columns to measurements table
ALTER TABLE measurements 
ADD COLUMN f1 FLOAT,
ADD COLUMN f2 FLOAT,
ADD COLUMN f3 FLOAT,
ADD COLUMN f4 FLOAT,
ADD COLUMN f5 FLOAT,
ADD COLUMN f6 FLOAT,
ADD COLUMN f7 FLOAT;

-- Add comments to the new columns
COMMENT ON COLUMN measurements.f1 IS 'Frequency phase 1 (Hz)';
COMMENT ON COLUMN measurements.f2 IS 'Frequency phase 2 (Hz)';
COMMENT ON COLUMN measurements.f3 IS 'Frequency phase 3 (Hz)';
COMMENT ON COLUMN measurements.f4 IS 'Frequency phase 4 (Hz)';
COMMENT ON COLUMN measurements.f5 IS 'Frequency phase 5 (Hz)';
COMMENT ON COLUMN measurements.f6 IS 'Frequency phase 6 (Hz)';
COMMENT ON COLUMN measurements.f7 IS 'Frequency phase 7 (Hz)';
