-- Migration 003: Add Google Drive integration to teams
-- Adds folder and document tracking for team organization

-- Add Google Drive fields to teams table
ALTER TABLE teams
ADD COLUMN IF NOT EXISTS drive_folder_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS overview_doc_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS overview_doc_url TEXT,
ADD COLUMN IF NOT EXISTS roster_sheet_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS roster_sheet_url TEXT;

-- Create indexes for Drive lookups
CREATE INDEX IF NOT EXISTS idx_teams_drive_folder ON teams(drive_folder_id);
CREATE INDEX IF NOT EXISTS idx_teams_roster_sheet ON teams(roster_sheet_id);

-- Comments for documentation
COMMENT ON COLUMN teams.drive_folder_id IS 'Google Drive folder ID for team documents';
COMMENT ON COLUMN teams.overview_doc_id IS 'Google Docs ID for team overview document';
COMMENT ON COLUMN teams.overview_doc_url IS 'URL to team overview document';
COMMENT ON COLUMN teams.roster_sheet_id IS 'Google Sheets ID for Active Team Members roster';
COMMENT ON COLUMN teams.roster_sheet_url IS 'URL to Active Team Members roster';
