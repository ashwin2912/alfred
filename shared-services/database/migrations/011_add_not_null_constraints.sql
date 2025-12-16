-- Migration: 011_add_not_null_constraints.sql
-- Purpose: Add NOT NULL constraints to critical columns to prevent data integrity issues
-- Priority: 🔴 CRITICAL
-- Author: Database Hardening Phase
-- Date: 2024-12-14

-- ============================================================================
-- DESCRIPTION
-- ============================================================================
-- This migration adds NOT NULL constraints to columns that should never be null.
-- Before adding constraints, we backfill any NULL values with sensible defaults.
--
-- Affected tables:
-- - teams: team_lead_id must always exist
-- - team_memberships: role must always be set
-- - clickup_lists: team_id must always be set
-- - pending_onboarding: email and name must be set
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. TEAMS TABLE - Ensure every team has a team lead
-- ============================================================================

-- First, set team_lead_id to the first member who joined the team
-- (or the member with the earliest joined_at in team_memberships)
UPDATE teams SET team_lead_id = (
    SELECT tm.member_id
    FROM team_memberships tm
    WHERE tm.team_id = teams.id
    AND tm.is_active = true
    ORDER BY tm.joined_at ASC
    LIMIT 1
) WHERE team_lead_id IS NULL;

-- If still null (team has no members), we can't add the constraint yet
-- Log teams without leads for manual review
DO $$
DECLARE
    teams_without_leads INTEGER;
BEGIN
    SELECT COUNT(*) INTO teams_without_leads
    FROM teams
    WHERE team_lead_id IS NULL;

    IF teams_without_leads > 0 THEN
        RAISE WARNING 'Found % teams without team leads. These must be assigned before applying NOT NULL constraint.', teams_without_leads;
        RAISE EXCEPTION 'Cannot apply NOT NULL constraint to teams.team_lead_id until all teams have leads assigned.';
    END IF;
END $$;

-- Add NOT NULL constraint
ALTER TABLE teams
ALTER COLUMN team_lead_id SET NOT NULL;

COMMENT ON COLUMN teams.team_lead_id IS 'Team lead member ID - REQUIRED (NOT NULL enforced)';

-- ============================================================================
-- 2. TEAM_MEMBERSHIPS TABLE - Ensure every membership has a role
-- ============================================================================

-- Set default role for any null values
UPDATE team_memberships
SET role = 'Team Member'
WHERE role IS NULL OR role = '';

-- Add NOT NULL constraint
ALTER TABLE team_memberships
ALTER COLUMN role SET NOT NULL;

COMMENT ON COLUMN team_memberships.role IS 'Member role in team - REQUIRED (NOT NULL enforced)';

-- ============================================================================
-- 3. CLICKUP_LISTS TABLE - Ensure every list belongs to a team
-- ============================================================================

-- Check for orphaned lists (no team_id)
DO $$
DECLARE
    orphaned_lists INTEGER;
BEGIN
    SELECT COUNT(*) INTO orphaned_lists
    FROM clickup_lists
    WHERE team_id IS NULL;

    IF orphaned_lists > 0 THEN
        RAISE WARNING 'Found % ClickUp lists without team_id. These will be deleted.', orphaned_lists;
    END IF;
END $$;

-- Delete orphaned lists (safer than assigning to random team)
DELETE FROM clickup_lists WHERE team_id IS NULL;

-- Add NOT NULL constraint
ALTER TABLE clickup_lists
ALTER COLUMN team_id SET NOT NULL;

COMMENT ON COLUMN clickup_lists.team_id IS 'Team that owns this list - REQUIRED (NOT NULL enforced)';

-- ============================================================================
-- 4. PENDING_ONBOARDING TABLE - Ensure email and name are always set
-- ============================================================================

-- Check for records without email (should never happen)
DO $$
DECLARE
    missing_emails INTEGER;
BEGIN
    SELECT COUNT(*) INTO missing_emails
    FROM pending_onboarding
    WHERE email IS NULL OR email = '';

    IF missing_emails > 0 THEN
        RAISE EXCEPTION 'Found % pending_onboarding records without email. Manual intervention required.', missing_emails;
    END IF;
END $$;

-- Add NOT NULL constraints
ALTER TABLE pending_onboarding
ALTER COLUMN email SET NOT NULL;

ALTER TABLE pending_onboarding
ALTER COLUMN name SET NOT NULL;

COMMENT ON COLUMN pending_onboarding.email IS 'Applicant email - REQUIRED (NOT NULL enforced)';
COMMENT ON COLUMN pending_onboarding.name IS 'Applicant name - REQUIRED (NOT NULL enforced)';

-- ============================================================================
-- 5. CLICKUP_LISTS TABLE - Ensure list_name is always set
-- ============================================================================

-- Set default name for any null values
UPDATE clickup_lists
SET list_name = 'Unnamed List'
WHERE list_name IS NULL OR list_name = '';

-- Add NOT NULL constraint
ALTER TABLE clickup_lists
ALTER COLUMN list_name SET NOT NULL;

COMMENT ON COLUMN clickup_lists.list_name IS 'ClickUp list name - REQUIRED (NOT NULL enforced)';

-- ============================================================================
-- 6. CLICKUP_LISTS TABLE - Ensure clickup_list_id is always set
-- ============================================================================

-- Check for lists without ClickUp ID (should never happen)
DO $$
DECLARE
    missing_list_ids INTEGER;
BEGIN
    SELECT COUNT(*) INTO missing_list_ids
    FROM clickup_lists
    WHERE clickup_list_id IS NULL OR clickup_list_id = '';

    IF missing_list_ids > 0 THEN
        RAISE EXCEPTION 'Found % clickup_lists records without clickup_list_id. Manual intervention required.', missing_list_ids;
    END IF;
END $$;

-- Add NOT NULL constraint
ALTER TABLE clickup_lists
ALTER COLUMN clickup_list_id SET NOT NULL;

COMMENT ON COLUMN clickup_lists.clickup_list_id IS 'ClickUp list ID - REQUIRED (NOT NULL enforced)';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify constraints were added successfully
DO $$
BEGIN
    -- Check teams.team_lead_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'teams'
        AND column_name = 'team_lead_id'
        AND is_nullable = 'NO'
    ) THEN
        RAISE EXCEPTION 'Failed to add NOT NULL constraint to teams.team_lead_id';
    END IF;

    -- Check team_memberships.role
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'team_memberships'
        AND column_name = 'role'
        AND is_nullable = 'NO'
    ) THEN
        RAISE EXCEPTION 'Failed to add NOT NULL constraint to team_memberships.role';
    END IF;

    -- Check clickup_lists.team_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'clickup_lists'
        AND column_name = 'team_id'
        AND is_nullable = 'NO'
    ) THEN
        RAISE EXCEPTION 'Failed to add NOT NULL constraint to clickup_lists.team_id';
    END IF;

    RAISE NOTICE 'SUCCESS: All NOT NULL constraints added successfully';
END $$;

COMMIT;

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================
-- To rollback this migration, run:
--
-- BEGIN;
-- ALTER TABLE teams ALTER COLUMN team_lead_id DROP NOT NULL;
-- ALTER TABLE team_memberships ALTER COLUMN role DROP NOT NULL;
-- ALTER TABLE clickup_lists ALTER COLUMN team_id DROP NOT NULL;
-- ALTER TABLE clickup_lists ALTER COLUMN list_name DROP NOT NULL;
-- ALTER TABLE clickup_lists ALTER COLUMN clickup_list_id DROP NOT NULL;
-- ALTER TABLE pending_onboarding ALTER COLUMN email DROP NOT NULL;
-- ALTER TABLE pending_onboarding ALTER COLUMN name DROP NOT NULL;
-- COMMIT;
