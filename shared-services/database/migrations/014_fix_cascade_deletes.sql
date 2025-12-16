-- Migration: 014_fix_cascade_deletes.sql
-- Purpose: Fix foreign key constraints to prevent orphaned records
-- Priority: 🔴 CRITICAL
-- Author: Database Hardening Phase
-- Date: 2024-12-14

-- ============================================================================
-- DESCRIPTION
-- ============================================================================
-- This migration fixes ON DELETE behaviors for foreign key constraints.
-- Prevents orphaned records by changing SET NULL to CASCADE where appropriate.
--
-- Strategy:
-- - CASCADE: Auto-delete dependent records (for truly dependent data)
-- - SET NULL: Keep record but clear reference (for optional references)
-- - RESTRICT: Prevent deletion if dependents exist (for important data)
--
-- Changes:
-- 1. clickup_lists.team_id: SET NULL → CASCADE (lists belong to teams)
-- 2. team_memberships.member_id: Add CASCADE (memberships depend on members)
-- 3. team_memberships.team_id: Add CASCADE (memberships depend on teams)
-- 4. team_members.manager_id: Keep SET NULL (managers are optional)
-- 5. teams.parent_team_id: Keep SET NULL (parent is optional)
-- 6. teams.team_lead_id: Add RESTRICT (prevent deleting team lead)
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CLICKUP_LISTS TABLE - CASCADE on team deletion
-- ============================================================================

-- Current: ON DELETE SET NULL allows orphaned lists
-- Fix: ON DELETE CASCADE - when team deleted, delete its lists too

-- Drop existing constraint
ALTER TABLE clickup_lists
DROP CONSTRAINT IF EXISTS clickup_lists_team_id_fkey;

-- Add with CASCADE
ALTER TABLE clickup_lists
ADD CONSTRAINT clickup_lists_team_id_fkey
FOREIGN KEY (team_id)
REFERENCES teams(id)
ON DELETE CASCADE;

COMMENT ON CONSTRAINT clickup_lists_team_id_fkey ON clickup_lists IS
'FK to teams - CASCADE DELETE: when team is deleted, delete all its lists';

-- ============================================================================
-- 2. TEAM_MEMBERSHIPS TABLE - CASCADE on member/team deletion
-- ============================================================================

-- Drop existing constraints
ALTER TABLE team_memberships
DROP CONSTRAINT IF EXISTS team_memberships_member_id_fkey;

ALTER TABLE team_memberships
DROP CONSTRAINT IF EXISTS team_memberships_team_id_fkey;

-- Add CASCADE for member_id (if member deleted, remove all their memberships)
ALTER TABLE team_memberships
ADD CONSTRAINT team_memberships_member_id_fkey
FOREIGN KEY (member_id)
REFERENCES team_members(id)
ON DELETE CASCADE;

COMMENT ON CONSTRAINT team_memberships_member_id_fkey ON team_memberships IS
'FK to team_members - CASCADE DELETE: when member is deleted, delete all their team memberships';

-- Add CASCADE for team_id (if team deleted, remove all memberships)
ALTER TABLE team_memberships
ADD CONSTRAINT team_memberships_team_id_fkey
FOREIGN KEY (team_id)
REFERENCES teams(id)
ON DELETE CASCADE;

COMMENT ON CONSTRAINT team_memberships_team_id_fkey ON team_memberships IS
'FK to teams - CASCADE DELETE: when team is deleted, delete all memberships';

-- ============================================================================
-- 3. TEAM_MEMBERS TABLE - Keep SET NULL for optional manager
-- ============================================================================

-- manager_id should remain SET NULL (managers are optional)
-- When a manager is deleted, their direct reports should remain (manager_id → NULL)

ALTER TABLE team_members
DROP CONSTRAINT IF EXISTS team_members_manager_id_fkey;

ALTER TABLE team_members
ADD CONSTRAINT team_members_manager_id_fkey
FOREIGN KEY (manager_id)
REFERENCES team_members(id)
ON DELETE SET NULL;

COMMENT ON CONSTRAINT team_members_manager_id_fkey ON team_members IS
'FK to team_members (manager) - SET NULL: when manager is deleted, clear manager_id for their reports';

-- ============================================================================
-- 4. TEAMS TABLE - Add RESTRICT for team_lead_id
-- ============================================================================

-- Prevent deleting a team lead if they're still leading a team
-- Must reassign team lead before deleting the member

ALTER TABLE teams
DROP CONSTRAINT IF EXISTS teams_team_lead_id_fkey;

ALTER TABLE teams
ADD CONSTRAINT teams_team_lead_id_fkey
FOREIGN KEY (team_lead_id)
REFERENCES team_members(id)
ON DELETE RESTRICT;

COMMENT ON CONSTRAINT teams_team_lead_id_fkey ON teams IS
'FK to team_members - RESTRICT DELETE: cannot delete team lead while they lead a team (must reassign first)';

-- ============================================================================
-- 5. TEAMS TABLE - Keep SET NULL for optional parent_team_id
-- ============================================================================

-- parent_team_id should remain SET NULL (parent is optional)
-- When parent team deleted, child teams become top-level

ALTER TABLE teams
DROP CONSTRAINT IF EXISTS teams_parent_team_id_fkey;

ALTER TABLE teams
ADD CONSTRAINT teams_parent_team_id_fkey
FOREIGN KEY (parent_team_id)
REFERENCES teams(id)
ON DELETE SET NULL;

COMMENT ON CONSTRAINT teams_parent_team_id_fkey ON teams IS
'FK to teams (parent) - SET NULL: when parent team is deleted, child teams become top-level';

-- ============================================================================
-- 6. PROJECT_BRAINSTORMS TABLE - CASCADE on team deletion (if team_name is FK)
-- ============================================================================

-- Note: project_brainstorms.team_name is currently VARCHAR, not a FK
-- We'll add a comment for future refactoring but not modify structure now

COMMENT ON COLUMN project_brainstorms.team_name IS
'Team name (string) - FUTURE: Consider changing to team_id UUID FK with CASCADE';

-- ============================================================================
-- 7. PENDING_ONBOARDING TABLE - No FK constraints currently
-- ============================================================================

-- pending_onboarding has no FK constraints
-- team_name is just a string, not a reference
-- No changes needed

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    constraint_record RECORD;
BEGIN
    RAISE NOTICE 'Verifying foreign key constraints...';

    -- Check clickup_lists.team_id → CASCADE
    SELECT confdeltype INTO constraint_record
    FROM pg_constraint c
    JOIN pg_class r ON c.conrelid = r.oid
    WHERE r.relname = 'clickup_lists'
    AND c.conname = 'clickup_lists_team_id_fkey';

    IF constraint_record.confdeltype != 'c' THEN
        RAISE EXCEPTION 'clickup_lists.team_id should CASCADE on delete';
    END IF;

    -- Check team_memberships.member_id → CASCADE
    SELECT confdeltype INTO constraint_record
    FROM pg_constraint c
    JOIN pg_class r ON c.conrelid = r.oid
    WHERE r.relname = 'team_memberships'
    AND c.conname = 'team_memberships_member_id_fkey';

    IF constraint_record.confdeltype != 'c' THEN
        RAISE EXCEPTION 'team_memberships.member_id should CASCADE on delete';
    END IF;

    -- Check team_memberships.team_id → CASCADE
    SELECT confdeltype INTO constraint_record
    FROM pg_constraint c
    JOIN pg_class r ON c.conrelid = r.oid
    WHERE r.relname = 'team_memberships'
    AND c.conname = 'team_memberships_team_id_fkey';

    IF constraint_record.confdeltype != 'c' THEN
        RAISE EXCEPTION 'team_memberships.team_id should CASCADE on delete';
    END IF;

    -- Check team_members.manager_id → SET NULL
    SELECT confdeltype INTO constraint_record
    FROM pg_constraint c
    JOIN pg_class r ON c.conrelid = r.oid
    WHERE r.relname = 'team_members'
    AND c.conname = 'team_members_manager_id_fkey';

    IF constraint_record.confdeltype != 'n' THEN
        RAISE EXCEPTION 'team_members.manager_id should SET NULL on delete';
    END IF;

    -- Check teams.team_lead_id → RESTRICT
    SELECT confdeltype INTO constraint_record
    FROM pg_constraint c
    JOIN pg_class r ON c.conrelid = r.oid
    WHERE r.relname = 'teams'
    AND c.conname = 'teams_team_lead_id_fkey';

    IF constraint_record.confdeltype != 'r' THEN
        RAISE EXCEPTION 'teams.team_lead_id should RESTRICT on delete';
    END IF;

    -- Check teams.parent_team_id → SET NULL
    SELECT confdeltype INTO constraint_record
    FROM pg_constraint c
    JOIN pg_class r ON c.conrelid = r.oid
    WHERE r.relname = 'teams'
    AND c.conname = 'teams_parent_team_id_fkey';

    IF constraint_record.confdeltype != 'n' THEN
        RAISE EXCEPTION 'teams.parent_team_id should SET NULL on delete';
    END IF;

    RAISE NOTICE 'SUCCESS: All foreign key constraints updated correctly';
    RAISE NOTICE '';
    RAISE NOTICE 'Summary of CASCADE behaviors:';
    RAISE NOTICE '  ✅ clickup_lists.team_id → CASCADE (delete lists with team)';
    RAISE NOTICE '  ✅ team_memberships.member_id → CASCADE (delete memberships with member)';
    RAISE NOTICE '  ✅ team_memberships.team_id → CASCADE (delete memberships with team)';
    RAISE NOTICE '  ✅ team_members.manager_id → SET NULL (clear manager when deleted)';
    RAISE NOTICE '  ✅ teams.team_lead_id → RESTRICT (must reassign lead before delete)';
    RAISE NOTICE '  ✅ teams.parent_team_id → SET NULL (make child teams top-level)';
END $$;

COMMIT;

-- ============================================================================
-- TESTING SCENARIOS
-- ============================================================================
--
-- Test 1: Delete a team → should cascade to clickup_lists and team_memberships
-- BEGIN;
-- DELETE FROM teams WHERE name = 'Test Team';
-- -- Should delete all clickup_lists for this team
-- -- Should delete all team_memberships for this team
-- ROLLBACK;
--
-- Test 2: Delete a team member → should cascade to team_memberships
-- BEGIN;
-- DELETE FROM team_members WHERE email = 'test@example.com';
-- -- Should delete all team_memberships for this member
-- -- Should set manager_id to NULL for their direct reports
-- ROLLBACK;
--
-- Test 3: Try to delete a team lead → should fail (RESTRICT)
-- BEGIN;
-- DELETE FROM team_members WHERE id = (SELECT team_lead_id FROM teams LIMIT 1);
-- -- Should fail with FK constraint error
-- -- Must first reassign team lead or delete team
-- ROLLBACK;
--
-- Test 4: Delete a manager → should clear manager_id (SET NULL)
-- BEGIN;
-- DELETE FROM team_members WHERE id IN (
--     SELECT DISTINCT manager_id FROM team_members WHERE manager_id IS NOT NULL LIMIT 1
-- );
-- -- Should succeed and set manager_id to NULL for their reports
-- ROLLBACK;

-- ============================================================================
-- BEST PRACTICES SUMMARY
-- ============================================================================
--
-- Use CASCADE when:
-- - Child records have no meaning without parent (e.g., team_memberships without team)
-- - Data is truly dependent (e.g., lists belong to a team)
--
-- Use SET NULL when:
-- - Relationship is optional (e.g., manager, parent team)
-- - Child record can exist independently
--
-- Use RESTRICT when:
-- - Deletion would cause data loss or integrity issues
-- - User should explicitly handle dependents first (e.g., reassign team lead)
--
-- Use NO ACTION (default) when:
-- - Similar to RESTRICT but can be deferred until end of transaction
-- - Allows for more complex cascading scenarios

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================
-- To rollback this migration, run:
--
-- BEGIN;
-- -- Restore original constraints
-- ALTER TABLE clickup_lists DROP CONSTRAINT clickup_lists_team_id_fkey;
-- ALTER TABLE clickup_lists ADD CONSTRAINT clickup_lists_team_id_fkey
--   FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL;
--
-- ALTER TABLE team_memberships DROP CONSTRAINT team_memberships_member_id_fkey;
-- ALTER TABLE team_memberships ADD CONSTRAINT team_memberships_member_id_fkey
--   FOREIGN KEY (member_id) REFERENCES team_members(id);
--
-- ALTER TABLE team_memberships DROP CONSTRAINT team_memberships_team_id_fkey;
-- ALTER TABLE team_memberships ADD CONSTRAINT team_memberships_team_id_fkey
--   FOREIGN KEY (team_id) REFERENCES teams(id);
--
-- ALTER TABLE teams DROP CONSTRAINT teams_team_lead_id_fkey;
-- ALTER TABLE teams ADD CONSTRAINT teams_team_lead_id_fkey
--   FOREIGN KEY (team_lead_id) REFERENCES team_members(id);
-- COMMIT;
