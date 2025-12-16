-- Migration 006: Minimal Project Brainstorms Table
-- Simplified table to track projects with minimal data

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- PROJECT BRAINSTORMS TABLE (MINIMAL)
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_brainstorms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User who created the project
    discord_user_id BIGINT NOT NULL,
    discord_username VARCHAR(100),

    -- Team association
    team_name VARCHAR(100),  -- Engineering, Product, Business

    -- Project basics
    title VARCHAR(255) NOT NULL,

    -- Google Doc link (where the breakdown lives)
    doc_id VARCHAR(255),
    doc_url TEXT,

    -- ClickUp integration (to be populated later)
    clickup_list_id VARCHAR(100),  -- ClickUp List ID for this project's tasks

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE project_brainstorms IS 'Minimal project tracking - links Discord users, Google Docs, and ClickUp';

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_project_brainstorms_discord_user ON project_brainstorms(discord_user_id);
CREATE INDEX IF NOT EXISTS idx_project_brainstorms_team ON project_brainstorms(team_name);
CREATE INDEX IF NOT EXISTS idx_project_brainstorms_doc_id ON project_brainstorms(doc_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update timestamp trigger
CREATE TRIGGER trigger_update_project_brainstorms_updated_at
    BEFORE UPDATE ON project_brainstorms
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
