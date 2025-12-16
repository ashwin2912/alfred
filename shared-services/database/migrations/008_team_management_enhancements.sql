-- Migration: Team Management Enhancements
-- Purpose: Add Discord and ClickUp integration fields to teams table
-- Date: 2024-12-13

-- Add Discord integration columns to teams table
ALTER TABLE teams ADD COLUMN IF NOT EXISTS discord_role_id BIGINT;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS discord_general_channel_id BIGINT;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS discord_standup_channel_id BIGINT;

-- Add ClickUp workspace integration columns
ALTER TABLE teams ADD COLUMN IF NOT EXISTS clickup_workspace_id VARCHAR(100);
ALTER TABLE teams ADD COLUMN IF NOT EXISTS clickup_space_id VARCHAR(100);
ALTER TABLE teams ADD COLUMN IF NOT EXISTS clickup_workspace_name VARCHAR(255);

-- Create team_memberships table for many-to-many relationship
-- This allows members to belong to multiple teams
CREATE TABLE IF NOT EXISTS team_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES team_members(id) ON DELETE CASCADE,
    role VARCHAR(100),  -- Role within the team (e.g., "Senior Engineer", "Product Manager")
    joined_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(team_id, member_id)
);

-- Create indexes for team_memberships
CREATE INDEX IF NOT EXISTS idx_team_memberships_team ON team_memberships(team_id);
CREATE INDEX IF NOT EXISTS idx_team_memberships_member ON team_memberships(member_id);
CREATE INDEX IF NOT EXISTS idx_team_memberships_active ON team_memberships(is_active);

-- Create function to get all teams for a member
CREATE OR REPLACE FUNCTION get_member_teams(member_id_param UUID)
RETURNS TABLE (
    team_id UUID,
    team_name VARCHAR(100),
    team_role VARCHAR(100),
    joined_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.name,
        tm.role,
        tm.joined_at
    FROM teams t
    JOIN team_memberships tm ON t.id = tm.team_id
    WHERE tm.member_id = member_id_param
    AND tm.is_active = true
    ORDER BY tm.joined_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Create function to get all members for a team
CREATE OR REPLACE FUNCTION get_team_member_list(team_id_param UUID)
RETURNS TABLE (
    member_id UUID,
    member_name VARCHAR(255),
    member_email VARCHAR(255),
    team_role VARCHAR(100),
    joined_at TIMESTAMP,
    discord_user_id BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.name,
        m.email,
        tm.role,
        tm.joined_at,
        m.discord_user_id
    FROM team_members m
    JOIN team_memberships tm ON m.id = tm.member_id
    WHERE tm.team_id = team_id_param
    AND tm.is_active = true
    ORDER BY tm.joined_at ASC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Add comment to describe the migration
COMMENT ON TABLE team_memberships IS 'Many-to-many relationship between teams and members, allowing members to belong to multiple teams';
COMMENT ON COLUMN teams.discord_role_id IS 'Discord role ID for this team';
COMMENT ON COLUMN teams.discord_general_channel_id IS 'Discord general channel ID for this team';
COMMENT ON COLUMN teams.discord_standup_channel_id IS 'Discord standup channel ID for this team';
COMMENT ON COLUMN teams.clickup_workspace_id IS 'ClickUp workspace ID for this team';
COMMENT ON COLUMN teams.clickup_space_id IS 'ClickUp space ID for this team';
COMMENT ON COLUMN teams.clickup_workspace_name IS 'ClickUp workspace name for display';
