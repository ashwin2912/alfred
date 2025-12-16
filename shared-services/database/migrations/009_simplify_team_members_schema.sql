-- Migration: Simplify team_members schema
-- Remove unused fields that are causing Pydantic validation errors
-- Date: 2024-12-14

-- Remove columns that don't exist in the actual table but are in Pydantic models
-- Or add columns that Pydantic expects but are missing

-- Check what columns actually exist first
-- You can run: SELECT column_name FROM information_schema.columns WHERE table_name = 'team_members';

-- For now, let's ensure the table has ONLY the fields we actually use:
-- Keep: id, user_id, discord_id, discord_username, name, email, phone, bio,
--       role, team, manager_id, start_date, status, clickup_api_token, created_at, updated_at
--       profile_doc_id, profile_url, clickup_user_id (needed for integrations)

-- Remove these if they exist (they're in the old model but not used):
ALTER TABLE team_members DROP COLUMN IF EXISTS availability_hours;
ALTER TABLE team_members DROP COLUMN IF EXISTS skills;
ALTER TABLE team_members DROP COLUMN IF EXISTS preferred_tasks;
ALTER TABLE team_members DROP COLUMN IF EXISTS links;
ALTER TABLE team_members DROP COLUMN IF EXISTS onboarded_at;
ALTER TABLE team_members DROP COLUMN IF EXISTS timezone;

-- Add columns we actually need if they don't exist
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Ensure these basic columns exist
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS user_id UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS discord_id BIGINT UNIQUE;
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS discord_username VARCHAR(100);
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL;
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS email VARCHAR(255) NOT NULL UNIQUE;
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS bio TEXT;
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS role VARCHAR(50);
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS team VARCHAR(100);
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS manager_id UUID REFERENCES team_members(id);
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS start_date DATE DEFAULT CURRENT_DATE;
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS clickup_api_token TEXT;

-- Add integration fields (important for Google Docs and ClickUp)
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS profile_doc_id VARCHAR(255);
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS profile_url TEXT;
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS clickup_user_id VARCHAR(100);

-- Add comment
COMMENT ON TABLE team_members IS 'Simplified team members table - essential fields plus integration IDs';
