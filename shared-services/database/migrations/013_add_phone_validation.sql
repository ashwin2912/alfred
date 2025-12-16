-- Migration: 013_add_phone_validation.sql
-- Purpose: Add phone number format validation
-- Priority: 🔴 CRITICAL
-- Author: Database Hardening Phase
-- Date: 2024-12-14

-- ============================================================================
-- DESCRIPTION
-- ============================================================================
-- This migration adds CHECK constraints to validate phone number format.
-- Supports two validation modes:
-- 1. E.164 format (strict): +[country code][number] (e.g., +14155552671)
-- 2. Flexible format: Allows common phone formats with spaces, dashes, parentheses
--
-- We'll use the flexible format by default for better UX.
--
-- Affected tables:
-- - team_members: phone validation
-- - pending_onboarding: phone validation
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. VALIDATE EXISTING DATA
-- ============================================================================

-- Check for invalid phone numbers in team_members (if not null)
DO $$
DECLARE
    invalid_phones INTEGER;
    sample_invalid TEXT;
BEGIN
    SELECT COUNT(*) INTO invalid_phones
    FROM team_members
    WHERE phone IS NOT NULL
    AND phone != ''
    AND phone !~ '^[\d\s\-\+\(\)\.]{7,20}$';

    IF invalid_phones > 0 THEN
        SELECT phone INTO sample_invalid
        FROM team_members
        WHERE phone IS NOT NULL
        AND phone != ''
        AND phone !~ '^[\d\s\-\+\(\)\.]{7,20}$'
        LIMIT 1;

        RAISE WARNING 'Found % team members with invalid phone format. Example: %', invalid_phones, sample_invalid;
        RAISE WARNING 'Valid formats: +1-555-123-4567, (555) 123-4567, +14155552671, etc.';
        RAISE NOTICE 'Setting invalid phone numbers to NULL...';

        -- Set invalid phones to NULL instead of blocking migration
        UPDATE team_members
        SET phone = NULL
        WHERE phone IS NOT NULL
        AND phone != ''
        AND phone !~ '^[\d\s\-\+\(\)\.]{7,20}$';
    END IF;
END $$;

-- Check for invalid phone numbers in pending_onboarding
DO $$
DECLARE
    invalid_phones INTEGER;
BEGIN
    SELECT COUNT(*) INTO invalid_phones
    FROM pending_onboarding
    WHERE phone IS NOT NULL
    AND phone != ''
    AND phone !~ '^[\d\s\-\+\(\)\.]{7,20}$';

    IF invalid_phones > 0 THEN
        RAISE NOTICE 'Found % pending onboarding requests with invalid phone format. Setting to NULL...', invalid_phones;

        -- Set invalid phones to NULL
        UPDATE pending_onboarding
        SET phone = NULL
        WHERE phone IS NOT NULL
        AND phone != ''
        AND phone !~ '^[\d\s\-\+\(\)\.]{7,20}$';
    END IF;
END $$;

-- ============================================================================
-- 2. ADD PHONE VALIDATION CONSTRAINTS
-- ============================================================================

-- Add flexible phone validation to team_members
-- Allows: digits, spaces, dashes, plus, parentheses, dots
-- Length: 7-20 characters (covers most international formats)
ALTER TABLE team_members
ADD CONSTRAINT valid_phone_format
CHECK (phone IS NULL OR phone ~ '^[\d\s\-\+\(\)\.]{7,20}$');

COMMENT ON CONSTRAINT valid_phone_format ON team_members IS
'Validates phone format: allows digits, spaces, dashes, plus, parentheses, dots. Length: 7-20 chars. Examples: +1-555-123-4567, (555) 123-4567';

-- Add phone validation to pending_onboarding
ALTER TABLE pending_onboarding
ADD CONSTRAINT valid_phone_format
CHECK (phone IS NULL OR phone ~ '^[\d\s\-\+\(\)\.]{7,20}$');

COMMENT ON CONSTRAINT valid_phone_format ON pending_onboarding IS
'Validates phone format: allows digits, spaces, dashes, plus, parentheses, dots. Length: 7-20 chars';

-- ============================================================================
-- 3. CREATE PHONE NORMALIZATION FUNCTION
-- ============================================================================

-- Function to extract digits only from phone number
CREATE OR REPLACE FUNCTION extract_phone_digits(phone_param VARCHAR)
RETURNS VARCHAR AS $$
BEGIN
    IF phone_param IS NULL THEN
        RETURN NULL;
    END IF;

    -- Remove all non-digit characters except leading +
    RETURN regexp_replace(phone_param, '[^\d+]', '', 'g');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION extract_phone_digits(VARCHAR) IS
'Extracts digits from phone number, preserving leading + for country code';

-- Function to format phone to E.164 (optional)
CREATE OR REPLACE FUNCTION format_phone_e164(phone_param VARCHAR, default_country_code VARCHAR DEFAULT '+1')
RETURNS VARCHAR AS $$
DECLARE
    digits_only VARCHAR;
BEGIN
    IF phone_param IS NULL THEN
        RETURN NULL;
    END IF;

    digits_only := extract_phone_digits(phone_param);

    -- If already has country code, return as-is
    IF digits_only LIKE '+%' THEN
        RETURN digits_only;
    END IF;

    -- If 10 digits (US format), add default country code
    IF length(digits_only) = 10 THEN
        RETURN default_country_code || digits_only;
    END IF;

    -- Otherwise return with + prefix if not already there
    IF digits_only NOT LIKE '+%' THEN
        RETURN '+' || digits_only;
    END IF;

    RETURN digits_only;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION format_phone_e164(VARCHAR, VARCHAR) IS
'Formats phone to E.164 standard (+[country][number]). Default country code: +1 (US)';

-- Function to format phone for display (US format)
CREATE OR REPLACE FUNCTION format_phone_us(phone_param VARCHAR)
RETURNS VARCHAR AS $$
DECLARE
    digits_only VARCHAR;
BEGIN
    IF phone_param IS NULL THEN
        RETURN NULL;
    END IF;

    -- Remove all non-digits
    digits_only := regexp_replace(phone_param, '\D', '', 'g');

    -- Format as (XXX) XXX-XXXX for 10-digit US numbers
    IF length(digits_only) = 10 THEN
        RETURN '(' || substring(digits_only, 1, 3) || ') ' ||
               substring(digits_only, 4, 3) || '-' ||
               substring(digits_only, 7, 4);
    END IF;

    -- Format as +X (XXX) XXX-XXXX for 11-digit numbers (with country code)
    IF length(digits_only) = 11 THEN
        RETURN '+' || substring(digits_only, 1, 1) || ' (' ||
               substring(digits_only, 2, 3) || ') ' ||
               substring(digits_only, 5, 3) || '-' ||
               substring(digits_only, 8, 4);
    END IF;

    -- Otherwise return as-is
    RETURN phone_param;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION format_phone_us(VARCHAR) IS
'Formats phone to US display format: (555) 123-4567';

-- ============================================================================
-- 4. ADD PHONE VALIDATION HELPER FUNCTION
-- ============================================================================

-- Function to validate E.164 format (strict)
CREATE OR REPLACE FUNCTION is_valid_e164_phone(phone_param VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    -- E.164: +[1-9][0-9]{1,14}
    -- Starts with +, then 1-15 digits
    RETURN phone_param ~ '^\+[1-9]\d{1,14}$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION is_valid_e164_phone(VARCHAR) IS
'Validates phone number in E.164 format: +[country code][number], 7-15 digits total';

-- ============================================================================
-- 5. CREATE PHONE CLEANING TRIGGER (OPTIONAL)
-- ============================================================================

-- Trigger function to clean phone numbers on insert/update
CREATE OR REPLACE FUNCTION clean_phone_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Trim whitespace
    IF NEW.phone IS NOT NULL THEN
        NEW.phone := TRIM(NEW.phone);

        -- If empty string, set to NULL
        IF NEW.phone = '' THEN
            NEW.phone := NULL;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to team_members
CREATE TRIGGER clean_team_member_phone
    BEFORE INSERT OR UPDATE OF phone ON team_members
    FOR EACH ROW
    EXECUTE FUNCTION clean_phone_trigger();

-- Apply trigger to pending_onboarding
CREATE TRIGGER clean_pending_onboarding_phone
    BEFORE INSERT OR UPDATE OF phone ON pending_onboarding
    FOR EACH ROW
    EXECUTE FUNCTION clean_phone_trigger();

COMMENT ON TRIGGER clean_team_member_phone ON team_members IS
'Automatically cleans phone numbers: trims whitespace, converts empty to NULL';

COMMENT ON TRIGGER clean_pending_onboarding_phone ON pending_onboarding IS
'Automatically cleans phone numbers: trims whitespace, converts empty to NULL';

-- ============================================================================
-- 6. CLEAN EXISTING PHONE DATA
-- ============================================================================

-- Trim whitespace from existing phones
UPDATE team_members
SET phone = TRIM(phone)
WHERE phone IS NOT NULL AND phone != TRIM(phone);

UPDATE pending_onboarding
SET phone = TRIM(phone)
WHERE phone IS NOT NULL AND phone != TRIM(phone);

-- Convert empty strings to NULL
UPDATE team_members
SET phone = NULL
WHERE phone = '';

UPDATE pending_onboarding
SET phone = NULL
WHERE phone = '';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Verify constraints exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.constraint_column_usage
        WHERE table_name = 'team_members'
        AND constraint_name = 'valid_phone_format'
    ) THEN
        RAISE EXCEPTION 'Failed to add phone validation constraint to team_members';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.constraint_column_usage
        WHERE table_name = 'pending_onboarding'
        AND constraint_name = 'valid_phone_format'
    ) THEN
        RAISE EXCEPTION 'Failed to add phone validation constraint to pending_onboarding';
    END IF;

    -- Test phone validation functions
    IF NOT is_valid_e164_phone('+14155552671') THEN
        RAISE EXCEPTION 'Phone validation function test failed';
    END IF;

    IF format_phone_us('5551234567') != '(555) 123-4567' THEN
        RAISE EXCEPTION 'Phone formatting function test failed';
    END IF;

    RAISE NOTICE 'SUCCESS: Phone validation constraints added successfully';
    RAISE NOTICE 'Phone cleaning triggers added successfully';
    RAISE NOTICE 'Phone formatting functions available: format_phone_us(), format_phone_e164(), is_valid_e164_phone()';
END $$;

COMMIT;

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================
--
-- Valid phone formats (will be accepted):
-- - +14155552671 (E.164)
-- - (415) 555-2671 (US format)
-- - 415-555-2671 (US format with dashes)
-- - 415.555.2671 (US format with dots)
-- - +44 20 7123 4567 (UK format)
--
-- Invalid formats (will be rejected):
-- - 123 (too short)
-- - abc-def-ghij (contains letters)
-- - 12345678901234567890123 (too long)
--
-- Format for display:
-- SELECT format_phone_us(phone) FROM team_members;
--
-- Extract digits only:
-- SELECT extract_phone_digits(phone) FROM team_members;
--
-- Convert to E.164:
-- SELECT format_phone_e164(phone, '+1') FROM team_members;

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================
-- To rollback this migration, run:
--
-- BEGIN;
-- DROP TRIGGER IF EXISTS clean_team_member_phone ON team_members;
-- DROP TRIGGER IF EXISTS clean_pending_onboarding_phone ON pending_onboarding;
-- DROP FUNCTION IF EXISTS clean_phone_trigger();
-- DROP FUNCTION IF EXISTS is_valid_e164_phone(VARCHAR);
-- DROP FUNCTION IF EXISTS format_phone_us(VARCHAR);
-- DROP FUNCTION IF EXISTS format_phone_e164(VARCHAR, VARCHAR);
-- DROP FUNCTION IF EXISTS extract_phone_digits(VARCHAR);
-- ALTER TABLE team_members DROP CONSTRAINT IF EXISTS valid_phone_format;
-- ALTER TABLE pending_onboarding DROP CONSTRAINT IF EXISTS valid_phone_format;
-- COMMIT;
