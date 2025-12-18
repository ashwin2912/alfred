-- ============================================================================
-- Migration 015: Add System Configuration Table
-- ============================================================================
-- Stores system-wide configuration like main roster sheet ID
-- ============================================================================

-- Create system_config table for singleton configuration
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    main_roster_sheet_id VARCHAR(255),
    main_roster_sheet_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT only_one_config CHECK (id = '00000000-0000-0000-0000-000000000001'::uuid)
);

-- Insert single row with fixed UUID (enforces singleton pattern)
INSERT INTO system_config (id)
VALUES ('00000000-0000-0000-0000-000000000001'::uuid)
ON CONFLICT (id) DO NOTHING;

-- Disable RLS for system_config (non-sensitive system data, service role only)
-- This table contains only system-wide config like spreadsheet IDs
-- Access is already controlled by service role key
ALTER TABLE system_config DISABLE ROW LEVEL SECURITY;

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_system_config_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_system_config_updated_at();

-- Comment
COMMENT ON TABLE system_config IS 'System-wide configuration (singleton table with one row)';
COMMENT ON COLUMN system_config.main_roster_sheet_id IS 'Google Sheets ID for main organization roster';
COMMENT ON COLUMN system_config.main_roster_sheet_url IS 'URL to main organization roster spreadsheet';
