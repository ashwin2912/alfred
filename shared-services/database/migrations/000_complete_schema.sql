-- Complete Alfred Database Schema
-- This is a complete schema with all migrations combined
-- Run this on a fresh database to set up everything at once

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Team Members Table
CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE,
    discord_id BIGINT UNIQUE,
    discord_username VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    bio TEXT,
    timezone VARCHAR(50),
    skills TEXT[] DEFAULT '{}',
    availability VARCHAR(50),
    clickup_api_token TEXT,
    role VARCHAR(50),
    team VARCHAR(100),
    manager_id UUID REFERENCES team_members(id),
    start_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for team_members
CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_team_members_email ON team_members(email);
CREATE INDEX IF NOT EXISTS idx_team_members_discord_username ON team_members(discord_username);
CREATE INDEX IF NOT EXISTS idx_team_members_discord_id ON team_members(discord_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members(team);
CREATE INDEX IF NOT EXISTS idx_team_members_role ON team_members(role);
CREATE INDEX IF NOT EXISTS idx_team_members_manager ON team_members(manager_id);

-- Teams Table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    team_lead_id UUID REFERENCES team_members(id),
    parent_team_id UUID REFERENCES teams(id),
    drive_folder_id VARCHAR(255),
    overview_doc_id VARCHAR(255),
    overview_doc_url TEXT,
    roster_sheet_id VARCHAR(255),
    roster_sheet_url TEXT,
    discord_role_id BIGINT,
    discord_general_channel_id BIGINT,
    discord_standup_channel_id BIGINT,
    clickup_workspace_id VARCHAR(100),
    clickup_space_id VARCHAR(100),
    clickup_workspace_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for teams
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
CREATE INDEX IF NOT EXISTS idx_teams_lead ON teams(team_lead_id);
CREATE INDEX IF NOT EXISTS idx_teams_parent ON teams(parent_team_id);

-- Roles Table
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    level INTEGER NOT NULL CHECK (level >= 1 AND level <= 5),
    description TEXT,
    permissions JSONB DEFAULT '[]'::jsonb,
    discord_role_id BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for roles
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
CREATE INDEX IF NOT EXISTS idx_roles_level ON roles(level);

-- Team Memberships Table (Many-to-Many)
CREATE TABLE IF NOT EXISTS team_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES team_members(id) ON DELETE CASCADE,
    role VARCHAR(100),
    joined_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(team_id, member_id)
);

-- Indexes for team_memberships
CREATE INDEX IF NOT EXISTS idx_team_memberships_team ON team_memberships(team_id);
CREATE INDEX IF NOT EXISTS idx_team_memberships_member ON team_memberships(member_id);
CREATE INDEX IF NOT EXISTS idx_team_memberships_active ON team_memberships(is_active);

-- Pending Onboarding Table
CREATE TABLE IF NOT EXISTS pending_onboarding (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    discord_id BIGINT NOT NULL,
    discord_username VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    bio TEXT,
    role VARCHAR(50),
    team VARCHAR(100),
    timezone VARCHAR(50),
    skills JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    submitted_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    reviewed_by UUID REFERENCES team_members(id),
    rejection_reason TEXT
);

-- Indexes for pending_onboarding
CREATE INDEX IF NOT EXISTS idx_pending_onboarding_discord ON pending_onboarding(discord_id);
CREATE INDEX IF NOT EXISTS idx_pending_onboarding_status ON pending_onboarding(status);
CREATE INDEX IF NOT EXISTS idx_pending_onboarding_email ON pending_onboarding(email);

-- ClickUp Lists Table
CREATE TABLE IF NOT EXISTS clickup_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clickup_list_id VARCHAR(100) NOT NULL UNIQUE,
    list_name VARCHAR(255) NOT NULL,
    team_id UUID REFERENCES teams(id),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for clickup_lists
CREATE INDEX IF NOT EXISTS idx_clickup_lists_team ON clickup_lists(team_id);
CREATE INDEX IF NOT EXISTS idx_clickup_lists_active ON clickup_lists(is_active);

-- Project Brainstorms Table
CREATE TABLE IF NOT EXISTS project_brainstorms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    discord_user_id BIGINT NOT NULL,
    discord_username VARCHAR(100),
    team_name VARCHAR(100),
    title VARCHAR(255) NOT NULL,
    doc_id VARCHAR(255),
    doc_url TEXT,
    clickup_list_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for project_brainstorms
CREATE INDEX IF NOT EXISTS idx_project_brainstorms_discord_user ON project_brainstorms(discord_user_id);
CREATE INDEX IF NOT EXISTS idx_project_brainstorms_team ON project_brainstorms(team_name);
CREATE INDEX IF NOT EXISTS idx_project_brainstorms_doc_id ON project_brainstorms(doc_id);

-- ============================================================================
-- DEFAULT DATA
-- ============================================================================

-- Insert default roles
INSERT INTO roles (name, level, description, permissions) VALUES
('Individual Contributor', 1, 'Team member focused on execution', '["view_own_tasks", "update_own_tasks", "view_team"]'::jsonb),
('Team Lead', 2, 'Leads a small team or project', '["view_own_tasks", "update_own_tasks", "view_team", "assign_tasks", "create_tasks"]'::jsonb),
('Manager', 3, 'Manages a team and reports', '["view_all_team", "manage_team", "approve_tasks", "assign_tasks", "create_tasks", "view_reports"]'::jsonb),
('Director', 4, 'Oversees multiple teams', '["view_all", "manage_teams", "approve_onboarding", "create_teams", "assign_managers"]'::jsonb),
('Executive', 5, 'C-level leadership', '["full_access", "manage_organization", "approve_all", "view_analytics"]'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- Insert default teams
INSERT INTO teams (name, description) VALUES
('Engineering', 'Software development and technical infrastructure'),
('Product', 'Product management and design'),
('Business', 'Business development and operations')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to get team member list
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
        m.discord_id
    FROM team_members m
    JOIN team_memberships tm ON m.id = tm.member_id
    WHERE tm.team_id = team_id_param
    AND tm.is_active = true
    ORDER BY tm.joined_at ASC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get all teams for a member
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

-- Function to get team list IDs for ClickUp filtering
CREATE OR REPLACE FUNCTION get_team_list_ids(team_id_param UUID)
RETURNS VARCHAR(100)[] AS $$
    SELECT ARRAY_AGG(clickup_list_id)
    FROM clickup_lists
    WHERE team_id = team_id_param AND is_active = true;
$$ LANGUAGE SQL STABLE;

-- Function to get team member count
CREATE OR REPLACE FUNCTION get_team_member_count(team_id_param UUID)
RETURNS INTEGER AS $$
    SELECT COUNT(*)::INTEGER
    FROM team_memberships
    WHERE team_id = team_id_param AND is_active = true;
$$ LANGUAGE SQL STABLE;

-- Function to get direct reports count
CREATE OR REPLACE FUNCTION get_direct_reports_count(manager_id_param UUID)
RETURNS INTEGER AS $$
    SELECT COUNT(*)::INTEGER
    FROM team_members
    WHERE manager_id = manager_id_param AND status = 'active';
$$ LANGUAGE SQL STABLE;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Team Hierarchy View
CREATE OR REPLACE VIEW team_hierarchy AS
WITH RECURSIVE team_tree AS (
    -- Base case: top-level teams
    SELECT
        id,
        name,
        parent_team_id,
        team_lead_id,
        1 as level,
        ARRAY[name]::VARCHAR(100)[] as path
    FROM teams
    WHERE parent_team_id IS NULL

    UNION ALL

    -- Recursive case: child teams
    SELECT
        t.id,
        t.name,
        t.parent_team_id,
        t.team_lead_id,
        tt.level + 1,
        (tt.path || t.name)::VARCHAR(100)[]
    FROM teams t
    INNER JOIN team_tree tt ON t.parent_team_id = tt.id
)
SELECT * FROM team_tree ORDER BY path;

-- Reporting Structure View
CREATE OR REPLACE VIEW reporting_structure AS
WITH RECURSIVE reports AS (
    -- Base case: executives (no manager)
    SELECT
        id,
        name,
        email,
        role,
        team,
        manager_id,
        1 as level,
        ARRAY[name]::VARCHAR(255)[] as chain
    FROM team_members
    WHERE manager_id IS NULL AND status = 'active'

    UNION ALL

    -- Recursive case: direct reports
    SELECT
        tm.id,
        tm.name,
        tm.email,
        tm.role,
        tm.team,
        tm.manager_id,
        r.level + 1,
        (r.chain || tm.name)::VARCHAR(255)[]
    FROM team_members tm
    INNER JOIN reports r ON tm.manager_id = r.id
    WHERE tm.status = 'active'
)
SELECT * FROM reports ORDER BY chain;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger to update team_members updated_at
CREATE OR REPLACE FUNCTION update_team_member_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_team_member_updated_at
    BEFORE UPDATE ON team_members
    FOR EACH ROW
    EXECUTE FUNCTION update_team_member_updated_at();

-- Trigger to update teams updated_at
CREATE OR REPLACE FUNCTION update_team_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_team_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION update_team_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on tables
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_onboarding ENABLE ROW LEVEL SECURITY;

-- Team Members RLS Policies
CREATE POLICY "Team members viewable by authenticated users" ON team_members
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Team members can update own profile" ON team_members
    FOR UPDATE
    USING (user_id = auth.uid());

-- Teams RLS Policies
CREATE POLICY "Teams are viewable by authenticated users" ON teams
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Teams can be managed by directors and above" ON teams
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM team_members tm
            INNER JOIN roles r ON tm.role = r.name
            WHERE tm.user_id = auth.uid()
            AND r.level >= 4
        )
    );

-- Roles RLS Policies
CREATE POLICY "Roles are viewable by authenticated users" ON roles
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- Team Memberships RLS Policies
CREATE POLICY "Team memberships are viewable by authenticated users" ON team_memberships
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Team memberships can be managed by managers and above" ON team_memberships
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM team_members tm
            INNER JOIN roles r ON tm.role = r.name
            WHERE tm.user_id = auth.uid()
            AND r.level >= 3
        )
    );

-- Pending Onboarding RLS Policies
CREATE POLICY "Pending onboarding viewable by directors and above" ON pending_onboarding
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM team_members tm
            INNER JOIN roles r ON tm.role = r.name
            WHERE tm.user_id = auth.uid()
            AND r.level >= 4
        )
    );

CREATE POLICY "Anyone can submit onboarding request" ON pending_onboarding
    FOR INSERT
    WITH CHECK (true);

-- System Configuration Table (singleton)
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

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE system_config IS 'System-wide configuration (singleton table with one row)';
COMMENT ON COLUMN system_config.main_roster_sheet_id IS 'Google Sheets ID for main organization roster';
COMMENT ON COLUMN system_config.main_roster_sheet_url IS 'URL to main organization roster spreadsheet';
COMMENT ON TABLE team_members IS 'All team members with profiles and metadata';
COMMENT ON TABLE teams IS 'Organizational teams with Discord and Google Drive integration';
COMMENT ON TABLE roles IS 'Role definitions with hierarchy levels';
COMMENT ON TABLE team_memberships IS 'Many-to-many relationship between teams and members';
COMMENT ON TABLE pending_onboarding IS 'Pending onboarding requests awaiting admin approval';
COMMENT ON TABLE clickup_lists IS 'ClickUp lists tracked per team for task filtering';
COMMENT ON TABLE project_brainstorms IS 'AI-generated project brainstorming sessions';

COMMENT ON COLUMN team_members.discord_id IS 'Discord user ID for integration';
COMMENT ON COLUMN team_members.status IS 'Member status: active, inactive, or pending';
COMMENT ON COLUMN teams.discord_role_id IS 'Discord role ID for this team';
COMMENT ON COLUMN teams.discord_general_channel_id IS 'Discord general channel ID for this team';
COMMENT ON COLUMN teams.discord_standup_channel_id IS 'Discord standup channel ID for this team';
COMMENT ON COLUMN teams.clickup_workspace_id IS 'ClickUp workspace ID for this team';
COMMENT ON COLUMN roles.level IS 'Hierarchy level: 1=IC, 2=Lead, 3=Manager, 4=Director, 5=Executive';
