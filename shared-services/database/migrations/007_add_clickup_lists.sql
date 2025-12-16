-- Migration 007: Add ClickUp List Management
-- Allows teams to configure which ClickUp lists are relevant to their projects

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CLICKUP LISTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS clickup_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- ClickUp identifiers
    clickup_list_id VARCHAR(100) NOT NULL UNIQUE,
    list_name VARCHAR(255) NOT NULL,
    clickup_folder_id VARCHAR(100),
    clickup_space_id VARCHAR(100),

    -- Team association
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,

    -- List metadata
    description TEXT,
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE clickup_lists IS 'ClickUp lists configured for each team - used to filter relevant tasks';
COMMENT ON COLUMN clickup_lists.clickup_list_id IS 'ClickUp list ID from API';
COMMENT ON COLUMN clickup_lists.is_active IS 'Whether this list should be shown to team members';

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_clickup_lists_clickup_id ON clickup_lists(clickup_list_id);
CREATE INDEX IF NOT EXISTS idx_clickup_lists_team ON clickup_lists(team_id);
CREATE INDEX IF NOT EXISTS idx_clickup_lists_active ON clickup_lists(is_active) WHERE is_active = true;

-- ============================================================================
-- UPDATE TEAMS TABLE
-- ============================================================================

-- Add ClickUp workspace configuration to teams
ALTER TABLE teams
ADD COLUMN IF NOT EXISTS clickup_workspace_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS clickup_space_id VARCHAR(100);

COMMENT ON COLUMN teams.clickup_workspace_id IS 'ClickUp workspace ID for this team';
COMMENT ON COLUMN teams.clickup_space_id IS 'ClickUp space ID for this team';

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_clickup_lists_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_clickup_lists_updated_at
    BEFORE UPDATE ON clickup_lists
    FOR EACH ROW
    EXECUTE FUNCTION update_clickup_lists_updated_at();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get active lists for a team
CREATE OR REPLACE FUNCTION get_team_clickup_lists(team_id_param UUID)
RETURNS TABLE (
    list_id VARCHAR(100),
    list_name VARCHAR(255),
    description TEXT
) AS $$
    SELECT
        clickup_list_id,
        list_name,
        description
    FROM clickup_lists
    WHERE team_id = team_id_param
    AND is_active = true
    ORDER BY list_name;
$$ LANGUAGE SQL STABLE;

-- Function to get active lists for a team by team name
CREATE OR REPLACE FUNCTION get_team_clickup_lists_by_name(team_name_param VARCHAR)
RETURNS TABLE (
    list_id VARCHAR(100),
    list_name VARCHAR(255),
    description TEXT
) AS $$
    SELECT
        cl.clickup_list_id,
        cl.list_name,
        cl.description
    FROM clickup_lists cl
    INNER JOIN teams t ON cl.team_id = t.id
    WHERE t.name = team_name_param
    AND cl.is_active = true
    ORDER BY cl.list_name;
$$ LANGUAGE SQL STABLE;

-- Function to get all active list IDs for a team (for filtering)
CREATE OR REPLACE FUNCTION get_team_list_ids(team_id_param UUID)
RETURNS VARCHAR(100)[] AS $$
    SELECT ARRAY_AGG(clickup_list_id)
    FROM clickup_lists
    WHERE team_id = team_id_param
    AND is_active = true;
$$ LANGUAGE SQL STABLE;

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE clickup_lists ENABLE ROW LEVEL SECURITY;

-- Anyone can view active lists
CREATE POLICY "Active ClickUp lists are viewable by authenticated users" ON clickup_lists
    FOR SELECT
    USING (auth.role() = 'authenticated' AND is_active = true);

-- Only Team Leads and above can manage lists
CREATE POLICY "ClickUp lists can be managed by Team Leads and above" ON clickup_lists
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM team_members tm
            INNER JOIN roles r ON tm.role = r.name
            WHERE tm.user_id = auth.uid()
            AND r.level >= 2  -- Team Lead or higher
        )
    );

-- ============================================================================
-- EXAMPLE DATA (commented out - uncomment to add sample data)
-- ============================================================================

-- Add example lists for Engineering team
-- INSERT INTO clickup_lists (clickup_list_id, list_name, team_id, description, clickup_space_id)
-- SELECT
--     '901106348428',
--     'Engineering Tasks',
--     id,
--     'Main task list for engineering team',
--     '90110634'
-- FROM teams WHERE name = 'Engineering'
-- ON CONFLICT (clickup_list_id) DO NOTHING;
