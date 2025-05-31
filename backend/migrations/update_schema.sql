-- Add frequency columns for each phase if they don't exist
DO $$
BEGIN
    -- Phase 1
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'measurements' AND column_name = 'f1') THEN
        ALTER TABLE measurements ADD COLUMN f1 FLOAT;
        COMMENT ON COLUMN measurements.f1 IS 'Frequency Phase 1 (Hz)';
    END IF;

    -- Phase 2
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'measurements' AND column_name = 'f2') THEN
        ALTER TABLE measurements ADD COLUMN f2 FLOAT;
        COMMENT ON COLUMN measurements.f2 IS 'Frequency Phase 2 (Hz)';
    END IF;

    -- Phase 3
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'measurements' AND column_name = 'f3') THEN
        ALTER TABLE measurements ADD COLUMN f3 FLOAT;
        COMMENT ON COLUMN measurements.f3 IS 'Frequency Phase 3 (Hz)';
    END IF;

    -- Phase 4
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'measurements' AND column_name = 'f4') THEN
        ALTER TABLE measurements ADD COLUMN f4 FLOAT;
        COMMENT ON COLUMN measurements.f4 IS 'Frequency Phase 4 (Hz)';
    END IF;

    -- Phase 5
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'measurements' AND column_name = 'f5') THEN
        ALTER TABLE measurements ADD COLUMN f5 FLOAT;
        COMMENT ON COLUMN measurements.f5 IS 'Frequency Phase 5 (Hz)';
    END IF;

    -- Phase 6
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'measurements' AND column_name = 'f6') THEN
        ALTER TABLE measurements ADD COLUMN f6 FLOAT;
        COMMENT ON COLUMN measurements.f6 IS 'Frequency Phase 6 (Hz)';
    END IF;

    -- Phase 7
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'measurements' AND column_name = 'f7') THEN
        ALTER TABLE measurements ADD COLUMN f7 FLOAT;
        COMMENT ON COLUMN measurements.f7 IS 'Frequency Phase 7 (Hz)';
    END IF;

    -- Drop the old frequency column if it exists
    IF EXISTS (SELECT 1 FROM information_schema.columns 
              WHERE table_name = 'measurements' AND column_name = 'frequency') THEN
        ALTER TABLE measurements DROP COLUMN frequency;
    END IF;
END
$$;
