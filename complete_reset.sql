-- Complete Database Reset
-- WARNING: This will delete ALL data from all tables
-- Use this to start fresh with a clean database
-- Updated: 2024-12-14 - Compatible with data integrity migrations (011-014)

-- ============================================================================
-- BEFORE RUNNING
-- ============================================================================
-- 1. Backup your database (Supabase has automatic backups)
-- 2. Verify you want to delete ALL data
-- 3. Consider exporting important data first
-- ============================================================================

DO $$
DECLARE
    team_memberships_count INTEGER;
    pending_onboarding_count INTEGER;
    team_members_count INTEGER;
    teams_count INTEGER;
    clickup_lists_count INTEGER;
    project_brainstorms_count INTEGER;
BEGIN
    RAISE NOTICE 'Starting database reset...';
    RAISE NOTICE '';

    -- ========================================================================
    -- Step 1: Delete dependent records first (respect foreign keys)
    -- ========================================================================

    -- Delete project brainstorms (no FK dependencies)
    DELETE FROM project_brainstorms;
    GET DIAGNOSTICS project_brainstorms_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % project brainstorms', project_brainstorms_count;

    -- Delete ClickUp lists (has FK to teams with CASCADE, but delete manually for safety)
    DELETE FROM clickup_lists;
    GET DIAGNOSTICS clickup_lists_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % ClickUp lists', clickup_lists_count;

    -- Delete team memberships (has FK to teams and team_members with CASCADE)
    DELETE FROM team_memberships;
    GET DIAGNOSTICS team_memberships_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % team memberships', team_memberships_count;

    -- Delete pending onboarding requests (no FK dependencies)
    DELETE FROM pending_onboarding;
    GET DIAGNOSTICS pending_onboarding_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % pending onboarding requests', pending_onboarding_count;

    -- ========================================================================
    -- Step 2: Temporarily disable NOT NULL constraint on team_lead_id
    -- ========================================================================
    -- Migration 011 added NOT NULL constraint to teams.team_lead_id
    -- We need to drop it temporarily to delete teams

    -- Drop NOT NULL constraint
    ALTER TABLE teams ALTER COLUMN team_lead_id DROP NOT NULL;
    RAISE NOTICE 'Temporarily disabled NOT NULL constraint on teams.team_lead_id';

    -- ========================================================================
    -- Step 3: Delete teams and team members
    -- ========================================================================

    -- Now we can delete teams (team_lead_id can be NULL temporarily)
    DELETE FROM teams;
    GET DIAGNOSTICS teams_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % teams', teams_count;

    -- Delete team members
    DELETE FROM team_members;
    GET DIAGNOSTICS team_members_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % team members', team_members_count;

    -- ========================================================================
    -- Step 4: Re-enable NOT NULL constraint on team_lead_id
    -- ========================================================================
    -- Restore the constraint for future inserts

    ALTER TABLE teams ALTER COLUMN team_lead_id SET NOT NULL;
    RAISE NOTICE 'Re-enabled NOT NULL constraint on teams.team_lead_id';

    -- Delete roles (if you want to reset role definitions too)
    -- Uncomment the line below if you want to delete roles
    -- DELETE FROM roles;
    -- RAISE NOTICE 'Deleted roles';

    -- ========================================================================
    -- Step 5: Verify cleanup
    -- ========================================================================

    SELECT COUNT(*) INTO team_memberships_count FROM team_memberships;
    SELECT COUNT(*) INTO pending_onboarding_count FROM pending_onboarding;
    SELECT COUNT(*) INTO team_members_count FROM team_members;
    SELECT COUNT(*) INTO teams_count FROM teams;
    SELECT COUNT(*) INTO clickup_lists_count FROM clickup_lists;
    SELECT COUNT(*) INTO project_brainstorms_count FROM project_brainstorms;

    RAISE NOTICE '';
    RAISE NOTICE '=== VERIFICATION ===';
    RAISE NOTICE 'team_memberships: % records remaining', team_memberships_count;
    RAISE NOTICE 'pending_onboarding: % records remaining', pending_onboarding_count;
    RAISE NOTICE 'team_members: % records remaining', team_members_count;
    RAISE NOTICE 'teams: % records remaining', teams_count;
    RAISE NOTICE 'clickup_lists: % records remaining', clickup_lists_count;
    RAISE NOTICE 'project_brainstorms: % records remaining', project_brainstorms_count;
    RAISE NOTICE '';

    IF team_memberships_count = 0
       AND pending_onboarding_count = 0
       AND team_members_count = 0
       AND teams_count = 0
       AND clickup_lists_count = 0
       AND project_brainstorms_count = 0 THEN
        RAISE NOTICE '✅ SUCCESS: All tables cleared successfully';
        RAISE NOTICE '';
        RAISE NOTICE 'Next steps:';
        RAISE NOTICE '  1. Delete Supabase auth.users if needed';
        RAISE NOTICE '  2. Run: python discord-bot/scripts/create_admin.py';
    ELSE
        RAISE WARNING '⚠️  WARNING: Some tables still have records';
    END IF;
END $$;

-- ============================================================================
-- IMPORTANT NOTES
-- ============================================================================
-- This script does NOT delete:
--
-- 1. Supabase auth.users
--    - Delete manually in Supabase Dashboard → Authentication → Users
--    - Or use SQL: DELETE FROM auth.users;
--
-- 2. Discord roles and channels
--    - Delete manually in Discord server settings
--
-- 3. Google Drive files and folders
--    - Delete manually in Google Drive
--    - Or use Google Drive API to clean up
--
-- 4. ClickUp tasks and lists
--    - Only removes references from database
--    - Tasks still exist in ClickUp workspace
--
-- 5. Database schema and migrations
--    - Tables, constraints, and indexes remain
--    - Only data is deleted
--
-- 6. Roles table (optional)
--    - Uncomment the DELETE FROM roles line above to clear roles
--    - Default roles (Individual Contributor, Team Lead, Manager, etc.) will be deleted
-- ============================================================================

-- ============================================================================
-- AFTER RUNNING THIS SCRIPT
-- ============================================================================
-- 1. Verify all tables are empty (output above shows counts)
-- 2. Delete Supabase auth.users manually if needed:
--    DELETE FROM auth.users;
-- 3. Create your first admin account:
--    python discord-bot/scripts/create_admin.py
-- 4. Start fresh with onboarding flow or create teams manually
-- ============================================================================
