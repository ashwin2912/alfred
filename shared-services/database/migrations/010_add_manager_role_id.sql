-- Migration: Add manager_role_id to teams table
-- Date: 2024-12-14

-- Add column for Discord manager role ID
ALTER TABLE teams ADD COLUMN IF NOT EXISTS discord_manager_role_id BIGINT;

-- Add comment
COMMENT ON COLUMN teams.discord_manager_role_id IS 'Discord role ID for team managers';
