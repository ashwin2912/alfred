-- Migration 005: Add team context to project brainstorms
-- Adds team and role information to track which team a project belongs to

-- Add team context columns
ALTER TABLE project_brainstorms
ADD COLUMN IF NOT EXISTS team_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS role_name VARCHAR(100);

-- Create index for team filtering
CREATE INDEX IF NOT EXISTS idx_project_brainstorms_team ON project_brainstorms(team_name);

-- Comments
COMMENT ON COLUMN project_brainstorms.team_name IS 'Team name (Engineering, Product, Business) - determines folder location';
COMMENT ON COLUMN project_brainstorms.role_name IS 'User role when creating project (e.g., Engineering Team Lead)';
