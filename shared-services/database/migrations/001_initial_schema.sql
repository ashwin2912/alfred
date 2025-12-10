-- Migration 001: Initial Schema - Complete Alfred Database
-- Run this on a fresh Supabase project to set up everything from scratch

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Roles: Hierarchy levels for team members
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

COMMENT ON TABLE roles IS 'Role definitions with hierarchy levels';
COMMENT ON COLUMN roles.level IS 'Hierarchy level: 1=IC, 2=Lead, 3=Manager, 4=Director, 5=Executive';

-- Teams: Organizational structure
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    team_lead_id UUID,  -- Will add FK constraint after team_members exists
    parent_team_id UUID REFERENCES teams(id),
    discord_role_id BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE teams IS 'Organizational teams structure';

-- Team Members: Core user data
CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE,  -- References auth.users
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    discord_username VARCHAR(100),
    discord_id BIGINT UNIQUE,
    clickup_user_id VARCHAR(100),
    clickup_api_token TEXT,
    bio TEXT,
    role VARCHAR(50),
    team VARCHAR(100),
    manager_id UUID REFERENCES team_members(id),
    timezone VARCHAR(50) DEFAULT 'UTC',
    availability_hours INTEGER DEFAULT 40 CHECK (availability_hours >= 0 AND availability_hours <= 168),
    skills JSONB DEFAULT '[]'::jsonb,
    preferred_tasks JSONB DEFAULT '[]'::jsonb,
    links JSONB DEFAULT '{}'::jsonb,
    profile_doc_id VARCHAR(255),
    profile_url TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending')),
    start_date DATE DEFAULT CURRENT_DATE,
    onboarded_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE team_members IS 'Core team member profiles and data';
COMMENT ON COLUMN team_members.discord_id IS 'Discord user ID for integration';
COMMENT ON COLUMN team_members.status IS 'Member status: active, inactive, or pending';

-- Now add the FK constraint for team_lead_id
ALTER TABLE teams ADD CONSTRAINT fk_teams_lead
    FOREIGN KEY (team_lead_id) REFERENCES team_members(id);

-- Team Memberships: Junction table for team assignments
CREATE TABLE IF NOT EXISTS team_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES team_members(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id),
    joined_at TIMESTAMP DEFAULT NOW(),
    left_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(team_id, member_id, is_active)
);

COMMENT ON TABLE team_memberships IS 'Junction table linking members to teams';

-- Pending Onboarding: Approval workflow
CREATE TABLE IF NOT EXISTS pending_onboarding (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    discord_id BIGINT NOT NULL,
    discord_username VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50),
    team VARCHAR(100),
    bio TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    skills JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    submitted_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    reviewed_by UUID REFERENCES team_members(id),
    rejection_reason TEXT
);

COMMENT ON TABLE pending_onboarding IS 'Pending onboarding requests awaiting approval';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Team Members Indexes
CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_team_members_email ON team_members(email);
CREATE INDEX IF NOT EXISTS idx_team_members_discord_username ON team_members(discord_username);
CREATE INDEX IF NOT EXISTS idx_team_members_discord_id ON team_members(discord_id);
CREATE INDEX IF NOT EXISTS idx_team_members_clickup_user_id ON team_members(clickup_user_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members(team);
CREATE INDEX IF NOT EXISTS idx_team_members_role ON team_members(role);
CREATE INDEX IF NOT EXISTS idx_team_members_manager ON team_members(manager_id);
CREATE INDEX IF NOT EXISTS idx_team_members_status ON team_members(status);

-- Teams Indexes
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
CREATE INDEX IF NOT EXISTS idx_teams_lead ON teams(team_lead_id);
CREATE INDEX IF NOT EXISTS idx_teams_parent ON teams(parent_team_id);

-- Roles Indexes
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
CREATE INDEX IF NOT EXISTS idx_roles_level ON roles(level);

-- Team Memberships Indexes
CREATE INDEX IF NOT EXISTS idx_team_memberships_team ON team_memberships(team_id);
CREATE INDEX IF NOT EXISTS idx_team_memberships_member ON team_memberships(member_id);
CREATE INDEX IF NOT EXISTS idx_team_memberships_active ON team_memberships(is_active) WHERE is_active = true;

-- Pending Onboarding Indexes
CREATE INDEX IF NOT EXISTS idx_pending_onboarding_discord ON pending_onboarding(discord_id);
CREATE INDEX IF NOT EXISTS idx_pending_onboarding_status ON pending_onboarding(status);
CREATE INDEX IF NOT EXISTS idx_pending_onboarding_email ON pending_onboarding(email);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Team Hierarchy View (Fixed recursive CTE)
CREATE OR REPLACE VIEW team_hierarchy AS
WITH RECURSIVE team_tree AS (
    -- Base case: top-level teams
    SELECT
        id,
        name,
        parent_team_id,
        team_lead_id,
        1 as level,
        ARRAY[name]::VARCHAR[] as path
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

-- Reporting Structure View (Fixed recursive CTE)
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
        ARRAY[name]::VARCHAR[] as chain
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

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

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

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update timestamp triggers
CREATE TRIGGER trigger_update_team_members_updated_at
    BEFORE UPDATE ON team_members
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_update_teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_update_roles_updated_at
    BEFORE UPDATE ON roles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_onboarding ENABLE ROW LEVEL SECURITY;

-- Team Members Policies
CREATE POLICY "Team members are viewable by authenticated users" ON team_members
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Users can update their own profile" ON team_members
    FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Service role can do anything" ON team_members
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- Teams Policies
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

-- Roles Policies
CREATE POLICY "Roles are viewable by authenticated users" ON roles
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- Team Memberships Policies
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

-- Pending Onboarding Policies
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

-- ============================================================================
-- SEED DATA
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
('Marketing', 'Marketing and growth initiatives'),
('Sales', 'Sales and business development'),
('Operations', 'Operations and administrative functions')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Uncomment these to verify the setup
-- SELECT * FROM roles ORDER BY level;
-- SELECT * FROM teams;
-- SELECT * FROM team_members LIMIT 5;
-- SELECT * FROM team_hierarchy;
-- SELECT * FROM reporting_structure;
