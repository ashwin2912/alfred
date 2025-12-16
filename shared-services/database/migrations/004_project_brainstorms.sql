-- Migration 004: Project Brainstorms
-- Tracks AI-generated project plans and links them to Google Docs and ClickUp

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- PROJECT BRAINSTORMS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_brainstorms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User who created the brainstorm
    discord_user_id BIGINT NOT NULL,
    discord_username VARCHAR(100),
    created_by UUID REFERENCES team_members(id),  -- Can be null if not onboarded yet

    -- Project details
    title VARCHAR(255) NOT NULL,
    raw_idea TEXT NOT NULL,  -- Original project idea from user

    -- AI-generated content (stored as JSONB for flexibility)
    ai_analysis JSONB,  -- Full analysis from AI (goals, scope, risks, etc.)

    -- Document links
    doc_id VARCHAR(255),  -- Google Doc ID
    doc_url TEXT,         -- Google Doc URL

    -- ClickUp integration
    clickup_list_id VARCHAR(100),    -- ClickUp List ID (when published)
    clickup_folder_id VARCHAR(100),  -- ClickUp Folder ID (optional)
    clickup_space_id VARCHAR(100),   -- ClickUp Space ID (optional)

    -- Status tracking
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP  -- When published to ClickUp
);

COMMENT ON TABLE project_brainstorms IS 'AI-generated project plans with links to Google Docs and ClickUp';
COMMENT ON COLUMN project_brainstorms.raw_idea IS 'Original project idea provided by user';
COMMENT ON COLUMN project_brainstorms.ai_analysis IS 'Full AI analysis (goals, scope, risks, milestones, tasks)';
COMMENT ON COLUMN project_brainstorms.status IS 'draft = planning, published = in ClickUp, archived = completed/cancelled';

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_project_brainstorms_discord_user ON project_brainstorms(discord_user_id);
CREATE INDEX IF NOT EXISTS idx_project_brainstorms_created_by ON project_brainstorms(created_by);
CREATE INDEX IF NOT EXISTS idx_project_brainstorms_status ON project_brainstorms(status);
CREATE INDEX IF NOT EXISTS idx_project_brainstorms_doc_id ON project_brainstorms(doc_id);
CREATE INDEX IF NOT EXISTS idx_project_brainstorms_clickup_list ON project_brainstorms(clickup_list_id);
CREATE INDEX IF NOT EXISTS idx_project_brainstorms_created_at ON project_brainstorms(created_at DESC);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update timestamp trigger
CREATE TRIGGER trigger_update_project_brainstorms_updated_at
    BEFORE UPDATE ON project_brainstorms
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE project_brainstorms ENABLE ROW LEVEL SECURITY;

-- Users can view their own brainstorms
CREATE POLICY "Users can view own brainstorms" ON project_brainstorms
    FOR SELECT
    USING (
        auth.uid() = created_by OR
        auth.jwt()->>'role' = 'service_role'
    );

-- Users can create their own brainstorms
CREATE POLICY "Users can create brainstorms" ON project_brainstorms
    FOR INSERT
    WITH CHECK (auth.uid() = created_by);

-- Users can update their own brainstorms
CREATE POLICY "Users can update own brainstorms" ON project_brainstorms
    FOR UPDATE
    USING (auth.uid() = created_by);

-- Managers can view all brainstorms
CREATE POLICY "Managers can view all brainstorms" ON project_brainstorms
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM team_members tm
            INNER JOIN roles r ON tm.role = r.name
            WHERE tm.user_id = auth.uid()
            AND r.level >= 3  -- Manager and above
        )
    );

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get brainstorm count by user
CREATE OR REPLACE FUNCTION get_user_brainstorm_count(user_id_param UUID)
RETURNS INTEGER AS $$
    SELECT COUNT(*)::INTEGER
    FROM project_brainstorms
    WHERE created_by = user_id_param;
$$ LANGUAGE SQL STABLE;

-- Function to get brainstorm count by status
CREATE OR REPLACE FUNCTION get_brainstorm_count_by_status(status_param VARCHAR)
RETURNS INTEGER AS $$
    SELECT COUNT(*)::INTEGER
    FROM project_brainstorms
    WHERE status = status_param;
$$ LANGUAGE SQL STABLE;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Uncomment to verify the setup
-- SELECT * FROM project_brainstorms LIMIT 5;
-- SELECT get_user_brainstorm_count('some-uuid');
-- SELECT get_brainstorm_count_by_status('draft');
