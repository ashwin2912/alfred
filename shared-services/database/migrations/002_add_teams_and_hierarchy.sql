-- Migration 002: Add Teams and Organizational Hierarchy
-- This migration adds team structure, roles, and Discord integration

-- Add new columns to team_members table
ALTER TABLE team_members
ADD COLUMN IF NOT EXISTS discord_id BIGINT UNIQUE,
ADD COLUMN IF NOT EXISTS role VARCHAR(50),
ADD COLUMN IF NOT EXISTS team VARCHAR(100),
ADD COLUMN IF NOT EXISTS manager_id UUID REFERENCES team_members(id),
ADD COLUMN IF NOT EXISTS start_date DATE DEFAULT CURRENT_DATE,
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending'));

-- Create index for Discord ID lookups
CREATE INDEX IF NOT EXISTS idx_team_members_discord_id ON team_members(discord_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members(team);
CREATE INDEX IF NOT EXISTS idx_team_members_role ON team_members(role);
CREATE INDEX IF NOT EXISTS idx_team_members_manager ON team_members(manager_id);

-- Create teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    team_lead_id UUID REFERENCES team_members(id),
    parent_team_id UUID REFERENCES teams(id),
    discord_role_id BIGINT,  -- Discord role ID for this team
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
CREATE INDEX IF NOT EXISTS idx_teams_lead ON teams(team_lead_id);
CREATE INDEX IF NOT EXISTS idx_teams_parent ON teams(parent_team_id);

-- Create roles table
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    level INTEGER NOT NULL CHECK (level >= 1 AND level <= 5),
    description TEXT,
    permissions JSONB DEFAULT '[]'::jsonb,
    discord_role_id BIGINT,  -- Discord role ID for this role level
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
CREATE INDEX IF NOT EXISTS idx_roles_level ON roles(level);

-- Create team_memberships junction table
CREATE TABLE IF NOT EXISTS team_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES team_members(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id),
    joined_at TIMESTAMP DEFAULT NOW(),
    left_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(team_id, member_id, is_active)  -- One active membership per team
);

CREATE INDEX IF NOT EXISTS idx_team_memberships_team ON team_memberships(team_id);
CREATE INDEX IF NOT EXISTS idx_team_memberships_member ON team_memberships(member_id);
CREATE INDEX IF NOT EXISTS idx_team_memberships_active ON team_memberships(is_active) WHERE is_active = true;

-- Create pending_onboarding table for approval workflow
CREATE TABLE IF NOT EXISTS pending_onboarding (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    discord_id BIGINT NOT NULL,
    discord_username VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50),
    team VARCHAR(100),
    bio TEXT,
    timezone VARCHAR(50),
    skills JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    submitted_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    reviewed_by UUID REFERENCES team_members(id),
    rejection_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_pending_onboarding_discord ON pending_onboarding(discord_id);
CREATE INDEX IF NOT EXISTS idx_pending_onboarding_status ON pending_onboarding(status);
CREATE INDEX IF NOT EXISTS idx_pending_onboarding_email ON pending_onboarding(email);

-- Insert default roles
INSERT INTO roles (name, level, description, permissions) VALUES
('Individual Contributor', 1, 'Team member focused on execution', '["view_own_tasks", "update_own_tasks", "view_team"]'::jsonb),
('Team Lead', 2, 'Leads a small team or project', '["view_own_tasks", "update_own_tasks", "view_team", "assign_tasks", "create_tasks"]'::jsonb),
('Manager', 3, 'Manages a team and reports', '["view_all_team", "manage_team", "approve_tasks", "assign_tasks", "create_tasks", "view_reports"]'::jsonb),
('Director', 4, 'Oversees multiple teams', '["view_all", "manage_teams", "approve_onboarding", "create_teams", "assign_managers"]'::jsonb),
('Executive', 5, 'C-level leadership', '["full_access", "manage_organization", "approve_all", "view_analytics"]'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- Insert default teams (examples)
INSERT INTO teams (name, description) VALUES
('Engineering', 'Software development and technical infrastructure'),
('Product', 'Product management and design'),
('Marketing', 'Marketing and growth initiatives'),
('Sales', 'Sales and business development'),
('Operations', 'Operations and administrative functions')
ON CONFLICT (name) DO NOTHING;

-- Create view for team hierarchy
CREATE OR REPLACE VIEW team_hierarchy AS
WITH RECURSIVE team_tree AS (
    -- Base case: top-level teams
    SELECT
        id,
        name,
        parent_team_id,
        team_lead_id,
        1 as level,
        ARRAY[name] as path
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
        tt.path || t.name
    FROM teams t
    INNER JOIN team_tree tt ON t.parent_team_id = tt.id
)
SELECT * FROM team_tree ORDER BY path;

-- Create view for reporting structure
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
        ARRAY[name] as chain
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
        r.chain || tm.name
    FROM team_members tm
    INNER JOIN reports r ON tm.manager_id = r.id
    WHERE tm.status = 'active'
)
SELECT * FROM reports ORDER BY chain;

-- Create function to get team members count
CREATE OR REPLACE FUNCTION get_team_member_count(team_id_param UUID)
RETURNS INTEGER AS $$
    SELECT COUNT(*)::INTEGER
    FROM team_memberships
    WHERE team_id = team_id_param AND is_active = true;
$$ LANGUAGE SQL STABLE;

-- Create function to get direct reports count
CREATE OR REPLACE FUNCTION get_direct_reports_count(manager_id_param UUID)
RETURNS INTEGER AS $$
    SELECT COUNT(*)::INTEGER
    FROM team_members
    WHERE manager_id = manager_id_param AND status = 'active';
$$ LANGUAGE SQL STABLE;

-- Add RLS policies for teams table
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;

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

-- Add RLS policies for roles table
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Roles are viewable by authenticated users" ON roles
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- Add RLS policies for team_memberships table
ALTER TABLE team_memberships ENABLE ROW LEVEL SECURITY;

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

-- Add RLS policies for pending_onboarding table
ALTER TABLE pending_onboarding ENABLE ROW LEVEL SECURITY;

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

-- Create trigger to update team updated_at
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

-- Comments for documentation
COMMENT ON TABLE teams IS 'Organizational teams structure';
COMMENT ON TABLE roles IS 'Role definitions with hierarchy levels';
COMMENT ON TABLE team_memberships IS 'Junction table linking members to teams';
COMMENT ON TABLE pending_onboarding IS 'Pending onboarding requests awaiting approval';
COMMENT ON COLUMN team_members.discord_id IS 'Discord user ID for integration';
COMMENT ON COLUMN team_members.status IS 'Member status: active, inactive, or pending';
COMMENT ON COLUMN roles.level IS 'Hierarchy level: 1=IC, 2=Lead, 3=Manager, 4=Director, 5=Executive';
