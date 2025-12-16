-- Migration: 012_add_email_validation.sql
-- Purpose: Add email format validation to prevent invalid emails
-- Priority: 🔴 CRITICAL
-- Author: Database Hardening Phase
-- Date: 2024-12-14

-- ============================================================================
-- DESCRIPTION
-- ============================================================================
-- This migration adds CHECK constraints to validate email format.
-- Ensures emails follow proper format: user@domain.tld
--
-- Affected tables:
-- - team_members: email must be valid format
-- - pending_onboarding: email must be valid format
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. VALIDATE EXISTING DATA
-- ============================================================================

-- Check for invalid emails in team_members
DO $$
DECLARE
    invalid_emails INTEGER;
BEGIN
    SELECT COUNT(*) INTO invalid_emails
    FROM team_members
    WHERE email IS NOT NULL
    AND email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';

    IF invalid_emails > 0 THEN
        RAISE WARNING 'Found % team members with invalid email format:', invalid_emails;
        RAISE WARNING 'Invalid emails: %', (
            SELECT string_agg(email, ', ')
            FROM team_members
            WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
            LIMIT 10
        );
        RAISE EXCEPTION 'Cannot apply email validation constraint. Fix invalid emails first.';
    END IF;
END $$;

-- Check for invalid emails in pending_onboarding
DO $$
DECLARE
    invalid_emails INTEGER;
BEGIN
    SELECT COUNT(*) INTO invalid_emails
    FROM pending_onboarding
    WHERE email IS NOT NULL
    AND email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';

    IF invalid_emails > 0 THEN
        RAISE WARNING 'Found % pending onboarding requests with invalid email format:', invalid_emails;
        RAISE WARNING 'Invalid emails: %', (
            SELECT string_agg(email, ', ')
            FROM pending_onboarding
            WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
            LIMIT 10
        );
        RAISE EXCEPTION 'Cannot apply email validation constraint. Fix invalid emails first.';
    END IF;
END $$;

-- ============================================================================
-- 2. ADD EMAIL VALIDATION CONSTRAINTS
-- ============================================================================

-- Add constraint to team_members
ALTER TABLE team_members
ADD CONSTRAINT valid_email_format
CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

COMMENT ON CONSTRAINT valid_email_format ON team_members IS
'Validates email format: user@domain.tld (allows letters, numbers, dots, underscores, percent, plus, hyphens)';

-- Add constraint to pending_onboarding
ALTER TABLE pending_onboarding
ADD CONSTRAINT valid_email_format
CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

COMMENT ON CONSTRAINT valid_email_format ON pending_onboarding IS
'Validates email format: user@domain.tld (allows letters, numbers, dots, underscores, percent, plus, hyphens)';

-- ============================================================================
-- 3. CREATE EMAIL DOMAIN WHITELIST TABLE (OPTIONAL)
-- ============================================================================

-- This table can be used to restrict signups to specific email domains
-- For example, only allow company emails (@yourcompany.com)
CREATE TABLE IF NOT EXISTS allowed_email_domains (
    domain VARCHAR(255) PRIMARY KEY,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES team_members(user_id)
);

COMMENT ON TABLE allowed_email_domains IS
'Whitelist of allowed email domains for company-only registration (optional feature)';

-- Example data (commented out - uncomment to enable domain restrictions)
-- INSERT INTO allowed_email_domains (domain, description) VALUES
-- ('yourcompany.com', 'Main company domain'),
-- ('subsidiary.com', 'Subsidiary company domain');

-- ============================================================================
-- 4. CREATE EMAIL VALIDATION HELPER FUNCTION
-- ============================================================================

-- Function to check if email domain is allowed
CREATE OR REPLACE FUNCTION is_allowed_email_domain(email_param VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    domain_count INTEGER;
BEGIN
    -- If no domains are configured, allow all valid emails
    SELECT COUNT(*) INTO domain_count FROM allowed_email_domains WHERE is_active = true;

    IF domain_count = 0 THEN
        RETURN TRUE;
    END IF;

    -- Check if email domain is in whitelist
    RETURN EXISTS (
        SELECT 1 FROM allowed_email_domains
        WHERE email_param ILIKE '%@' || domain
        AND is_active = true
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION is_allowed_email_domain(VARCHAR) IS
'Checks if email domain is in whitelist. Returns TRUE if no domains configured (allows all).';

-- Example: Add domain restriction constraint (commented out)
-- To enable domain restrictions, uncomment these lines:
--
-- ALTER TABLE team_members
-- ADD CONSTRAINT allowed_email_domain
-- CHECK (is_allowed_email_domain(email));
--
-- ALTER TABLE pending_onboarding
-- ADD CONSTRAINT allowed_email_domain
-- CHECK (is_allowed_email_domain(email));

-- ============================================================================
-- 5. CREATE EMAIL NORMALIZATION FUNCTION
-- ============================================================================

-- Function to normalize email (lowercase, trim whitespace)
CREATE OR REPLACE FUNCTION normalize_email(email_param VARCHAR)
RETURNS VARCHAR AS $$
BEGIN
    RETURN LOWER(TRIM(email_param));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION normalize_email(VARCHAR) IS
'Normalizes email by converting to lowercase and trimming whitespace';

-- ============================================================================
-- 6. UPDATE EXISTING EMAILS TO NORMALIZED FORMAT
-- ============================================================================

-- Normalize existing team_members emails
UPDATE team_members
SET email = normalize_email(email)
WHERE email != normalize_email(email);

-- Normalize existing pending_onboarding emails
UPDATE pending_onboarding
SET email = normalize_email(email)
WHERE email != normalize_email(email);

-- ============================================================================
-- 7. ADD TRIGGERS FOR EMAIL NORMALIZATION
-- ============================================================================

-- Trigger function to normalize email before insert/update
CREATE OR REPLACE FUNCTION normalize_email_trigger()
RETURNS TRIGGER AS $$
BEGIN
    NEW.email := normalize_email(NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to team_members
CREATE TRIGGER normalize_team_member_email
    BEFORE INSERT OR UPDATE OF email ON team_members
    FOR EACH ROW
    EXECUTE FUNCTION normalize_email_trigger();

-- Apply trigger to pending_onboarding
CREATE TRIGGER normalize_pending_onboarding_email
    BEFORE INSERT OR UPDATE OF email ON pending_onboarding
    FOR EACH ROW
    EXECUTE FUNCTION normalize_email_trigger();

COMMENT ON TRIGGER normalize_team_member_email ON team_members IS
'Automatically normalizes email to lowercase and trimmed on insert/update';

COMMENT ON TRIGGER normalize_pending_onboarding_email ON pending_onboarding IS
'Automatically normalizes email to lowercase and trimmed on insert/update';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Test email validation (should succeed)
    PERFORM 'test@example.com'::VARCHAR ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';

    -- Verify constraints exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.constraint_column_usage
        WHERE table_name = 'team_members'
        AND constraint_name = 'valid_email_format'
    ) THEN
        RAISE EXCEPTION 'Failed to add email validation constraint to team_members';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.constraint_column_usage
        WHERE table_name = 'pending_onboarding'
        AND constraint_name = 'valid_email_format'
    ) THEN
        RAISE EXCEPTION 'Failed to add email validation constraint to pending_onboarding';
    END IF;

    RAISE NOTICE 'SUCCESS: Email validation constraints added successfully';
    RAISE NOTICE 'Email normalization triggers added successfully';
END $$;

COMMIT;

-- ============================================================================
-- TESTING
-- ============================================================================
-- Test valid emails (should succeed):
-- INSERT INTO team_members (user_id, email, name) VALUES
--   (uuid_generate_v4(), 'test@example.com', 'Test User');
--   (uuid_generate_v4(), 'user.name+tag@company.co.uk', 'Test User 2');
--
-- Test invalid emails (should fail):
-- INSERT INTO team_members (user_id, email, name) VALUES
--   (uuid_generate_v4(), 'notanemail', 'Test User');  -- No @ or domain
--   (uuid_generate_v4(), 'missing@domain', 'Test User');  -- No TLD
--   (uuid_generate_v4(), '@nodomain.com', 'Test User');  -- No local part

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================
-- To rollback this migration, run:
--
-- BEGIN;
-- DROP TRIGGER IF EXISTS normalize_team_member_email ON team_members;
-- DROP TRIGGER IF EXISTS normalize_pending_onboarding_email ON pending_onboarding;
-- DROP FUNCTION IF EXISTS normalize_email_trigger();
-- DROP FUNCTION IF EXISTS normalize_email(VARCHAR);
-- DROP FUNCTION IF EXISTS is_allowed_email_domain(VARCHAR);
-- DROP TABLE IF EXISTS allowed_email_domains;
-- ALTER TABLE team_members DROP CONSTRAINT IF EXISTS valid_email_format;
-- ALTER TABLE pending_onboarding DROP CONSTRAINT IF EXISTS valid_email_format;
-- COMMIT;
