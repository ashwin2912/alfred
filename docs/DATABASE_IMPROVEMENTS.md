# Alfred Database - Best Practices & Improvements

Comprehensive analysis of the PostgreSQL/Supabase database schema with recommendations for production readiness, performance, and maintainability.

**Analysis Date**: December 14, 2024  
**Current Schema Version**: Migration 010  
**Database**: PostgreSQL 15+ (Supabase)

---

## Executive Summary

**Overall Assessment**: The schema is functionally complete but needs optimization and hardening for production scale.

**Key Findings**:
- ✅ Good: RLS policies exist, basic indexes present, foreign keys defined
- ⚠️ Needs Work: Missing composite indexes, no partitioning, weak constraints
- 🔴 Critical: RLS bypass possible, no audit logging, missing cascades

**Estimated Effort**: 1-2 days for critical fixes, 3-5 days for all improvements

---

## Priority Levels

- 🔴 **CRITICAL**: Data integrity/security risks (must fix before production)
- 🟠 **HIGH**: Performance/reliability issues (fix in first week)
- 🟡 **MEDIUM**: Code quality/maintainability (fix in first month)
- 🟢 **LOW**: Future optimizations (ongoing)

---

## 1. Security & Access Control 🔴 CRITICAL

### 1.1 RLS Policies Can Be Bypassed
**Issue**: Bot uses service role key which bypasses all RLS policies

**Files**: All tables with RLS enabled
**Current**: RLS policies defined but service_role ignores them

**Risk**: High - Malicious code could access/modify any data

**Fix**: Add application-level access control
```sql
-- Create function to check if user is admin
CREATE OR REPLACE FUNCTION is_admin(user_id_param UUID)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM team_members tm
        INNER JOIN roles r ON tm.role = r.name
        WHERE tm.user_id = user_id_param
        AND r.level >= 3  -- Manager and above
        AND tm.status = 'active'
    );
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Create function to check team membership
CREATE OR REPLACE FUNCTION is_team_member(user_id_param UUID, team_id_param UUID)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM team_memberships tm
        WHERE tm.member_id IN (
            SELECT id FROM team_members WHERE user_id = user_id_param
        )
        AND tm.team_id = team_id_param
        AND tm.is_active = true
    );
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Use in application code
-- Before any sensitive operation, check:
SELECT is_admin(current_user_id);
SELECT is_team_member(current_user_id, target_team_id);
```

**Recommendation**: Add middleware in data_service/client.py to enforce checks

---

### 1.2 Sensitive Data Not Encrypted
**Tables**: `team_members.clickup_api_token`, `team_members.phone`
**Issue**: API tokens stored in plain text

**Risk**: Medium - Token exposure if database compromised

**Fix**: Use Supabase Vault for secrets
```sql
-- Migration: 011_encrypt_sensitive_data.sql

-- Add encrypted column using pg_crypto
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Migrate tokens to vault references
ALTER TABLE team_members 
ADD COLUMN clickup_token_vault_id UUID;

-- Create migration function
CREATE OR REPLACE FUNCTION migrate_tokens_to_vault()
RETURNS void AS $$
DECLARE
    member RECORD;
BEGIN
    FOR member IN 
        SELECT id, clickup_api_token 
        FROM team_members 
        WHERE clickup_api_token IS NOT NULL
    LOOP
        -- Store in vault (pseudo-code - use Supabase vault API)
        -- vault_id := vault.create_secret('clickup_token_' || member.id, member.clickup_api_token);
        -- UPDATE team_members SET clickup_token_vault_id = vault_id WHERE id = member.id;
        NULL; -- Placeholder
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- After migration, drop plain text column
ALTER TABLE team_members DROP COLUMN clickup_api_token;
```

**Alternative**: Encrypt at application level before storing
```python
# In data_service/client.py
from cryptography.fernet import Fernet
import os

class DataService:
    def __init__(self, ...):
        self.encryption_key = Fernet(os.getenv('DB_ENCRYPTION_KEY'))
    
    def store_clickup_token(self, member_id: UUID, token: str):
        encrypted = self.encryption_key.encrypt(token.encode())
        # Store encrypted value
    
    def get_clickup_token(self, member_id: UUID) -> str:
        encrypted = # Fetch from DB
        return self.encryption_key.decrypt(encrypted).decode()
```

---

### 1.3 No Audit Logging
**Issue**: No record of who changed what and when

**Risk**: High - Cannot trace data modifications or security breaches

**Fix**: Add audit logging table and triggers
```sql
-- Migration: 012_add_audit_logging.sql

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB,
    changed_by UUID REFERENCES team_members(user_id),
    changed_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_audit_log_table ON audit_log(table_name);
CREATE INDEX idx_audit_log_record ON audit_log(record_id);
CREATE INDEX idx_audit_log_user ON audit_log(changed_by);
CREATE INDEX idx_audit_log_time ON audit_log(changed_at DESC);

-- Generic audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, record_id, action, new_data, changed_by)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', row_to_json(NEW)::jsonb, auth.uid());
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_by)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', row_to_json(OLD)::jsonb, row_to_json(NEW)::jsonb, auth.uid());
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_data, changed_by)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', row_to_json(OLD)::jsonb, auth.uid());
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply to sensitive tables
CREATE TRIGGER team_members_audit
    AFTER INSERT OR UPDATE OR DELETE ON team_members
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER teams_audit
    AFTER INSERT OR UPDATE OR DELETE ON teams
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER team_memberships_audit
    AFTER INSERT OR UPDATE OR DELETE ON team_memberships
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

**Retention Policy**:
```sql
-- Auto-delete audit logs older than 90 days
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM audit_log WHERE changed_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- Schedule with pg_cron (if available) or cron job
-- SELECT cron.schedule('cleanup-audit-logs', '0 2 * * *', 'SELECT cleanup_old_audit_logs()');
```

---

## 2. Data Integrity & Constraints 🔴 CRITICAL

### 2.1 Missing NOT NULL Constraints
**Issue**: Important columns allow NULL when they shouldn't

**Examples**:
- `teams.team_lead_id` - Team should always have a lead
- `team_memberships.role` - Membership should have a role
- `clickup_lists.team_id` - List should belong to a team

**Fix**: Add NOT NULL constraints
```sql
-- Migration: 013_add_not_null_constraints.sql

-- Teams must have a team lead (set default first if needed)
UPDATE teams SET team_lead_id = (
    SELECT tm.member_id 
    FROM team_memberships tm 
    WHERE tm.team_id = teams.id 
    ORDER BY tm.joined_at ASC 
    LIMIT 1
) WHERE team_lead_id IS NULL;

ALTER TABLE teams ALTER COLUMN team_lead_id SET NOT NULL;

-- Team memberships must have a role
UPDATE team_memberships 
SET role = 'Team Member' 
WHERE role IS NULL OR role = '';

ALTER TABLE team_memberships ALTER COLUMN role SET NOT NULL;

-- ClickUp lists must belong to a team
DELETE FROM clickup_lists WHERE team_id IS NULL;  -- Or set to default team
ALTER TABLE clickup_lists ALTER COLUMN team_id SET NOT NULL;

-- Pending onboarding must have contact info
ALTER TABLE pending_onboarding ALTER COLUMN email SET NOT NULL;
ALTER TABLE pending_onboarding ALTER COLUMN name SET NOT NULL;
```

---

### 2.2 Weak Email Validation
**Tables**: `team_members.email`, `pending_onboarding.email`
**Current**: No format validation, just UNIQUE constraint

**Fix**: Add email format validation
```sql
-- Add email validation constraint
ALTER TABLE team_members 
ADD CONSTRAINT valid_email_format 
CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$');

ALTER TABLE pending_onboarding 
ADD CONSTRAINT valid_email_format 
CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$');

-- Add domain whitelist (optional for company emails only)
CREATE TABLE allowed_email_domains (
    domain VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO allowed_email_domains (domain) VALUES
('yourdomain.com'),
('yourcompany.com');

-- Function to check email domain
CREATE OR REPLACE FUNCTION is_allowed_email_domain(email_param VARCHAR)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM allowed_email_domains
        WHERE email_param ILIKE '%@' || domain
    );
$$ LANGUAGE SQL STABLE;

-- Add check constraint (optional)
-- ALTER TABLE team_members 
-- ADD CONSTRAINT allowed_email_domain 
-- CHECK (is_allowed_email_domain(email));
```

---

### 2.3 Missing Phone Number Validation
**Table**: `team_members.phone`, `pending_onboarding.phone`
**Current**: VARCHAR(20) with no format validation

**Fix**: Add phone validation
```sql
-- Phone number validation (E.164 format)
ALTER TABLE team_members 
ADD CONSTRAINT valid_phone_format 
CHECK (phone IS NULL OR phone ~ '^\+[1-9]\d{1,14}$');

ALTER TABLE pending_onboarding 
ADD CONSTRAINT valid_phone_format 
CHECK (phone IS NULL OR phone ~ '^\+[1-9]\d{1,14}$');

-- Alternative: More flexible validation
-- CHECK (phone IS NULL OR phone ~ '^[\d\s\-\+\(\)\.]{7,20}$');
```

---

### 2.4 Orphaned Records Possible
**Issue**: ON DELETE SET NULL allows orphaned records

**Example**: `clickup_lists.team_id` uses `ON DELETE SET NULL`
- If team deleted, lists become orphaned (team_id = NULL)
- Can't query which team they belong to
- Violates referential integrity

**Fix**: Change to CASCADE or RESTRICT
```sql
-- Migration: 014_fix_cascade_deletes.sql

-- Drop existing constraint
ALTER TABLE clickup_lists 
DROP CONSTRAINT clickup_lists_team_id_fkey;

-- Add with CASCADE (deletes lists when team deleted)
ALTER TABLE clickup_lists 
ADD CONSTRAINT clickup_lists_team_id_fkey 
FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;

-- OR use RESTRICT (prevents team deletion if lists exist)
-- ADD CONSTRAINT clickup_lists_team_id_fkey 
-- FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE RESTRICT;

-- Same for other weak FKs
ALTER TABLE team_members 
DROP CONSTRAINT IF EXISTS team_members_manager_id_fkey,
ADD CONSTRAINT team_members_manager_id_fkey 
FOREIGN KEY (manager_id) REFERENCES team_members(id) ON DELETE SET NULL;  -- OK for managers

-- Team memberships should cascade
ALTER TABLE team_memberships 
DROP CONSTRAINT IF EXISTS team_memberships_member_id_fkey;

ALTER TABLE team_memberships 
ADD CONSTRAINT team_memberships_member_id_fkey 
FOREIGN KEY (member_id) REFERENCES team_members(id) ON DELETE CASCADE;
```

**Decision Matrix**:
- `CASCADE`: Auto-delete dependent records (use for truly dependent data)
- `SET NULL`: Keep record but clear reference (use for optional references)
- `RESTRICT`: Prevent deletion if dependents exist (safest for important data)

---

## 3. Performance & Indexing 🟠 HIGH

### 3.1 Missing Composite Indexes
**Issue**: Queries often filter by multiple columns but indexes don't support it

**Examples**:
```sql
-- Common query patterns without composite indexes:
-- 1. Find active team members
SELECT * FROM team_members WHERE team = 'Engineering' AND status = 'active';
-- Missing: (team, status)

-- 2. Find active team memberships
SELECT * FROM team_memberships WHERE team_id = ? AND is_active = true;
-- Missing: (team_id, is_active)

-- 3. Find pending onboarding by status and time
SELECT * FROM pending_onboarding WHERE status = 'pending' ORDER BY submitted_at DESC;
-- Missing: (status, submitted_at)
```

**Fix**: Add composite indexes
```sql
-- Migration: 015_add_composite_indexes.sql

-- Team members: common queries
CREATE INDEX idx_team_members_team_status 
ON team_members(team, status) 
WHERE status = 'active';  -- Partial index for active only

CREATE INDEX idx_team_members_status_created 
ON team_members(status, created_at DESC);

-- Team memberships: common queries
CREATE INDEX idx_team_memberships_team_active 
ON team_memberships(team_id, is_active) 
WHERE is_active = true;  -- Partial index

CREATE INDEX idx_team_memberships_member_active 
ON team_memberships(member_id, is_active) 
WHERE is_active = true;

-- Pending onboarding: admin dashboard queries
CREATE INDEX idx_pending_onboarding_status_submitted 
ON pending_onboarding(status, submitted_at DESC) 
WHERE status = 'pending';  -- Most common query

CREATE INDEX idx_pending_onboarding_email_status 
ON pending_onboarding(email, status);

-- ClickUp lists: team filtering
CREATE INDEX idx_clickup_lists_team_active 
ON clickup_lists(team_id, is_active) 
WHERE is_active = true;

-- Project brainstorms: user queries
CREATE INDEX idx_project_brainstorms_user_created 
ON project_brainstorms(discord_user_id, created_at DESC);

CREATE INDEX idx_project_brainstorms_team_created 
ON project_brainstorms(team_name, created_at DESC);
```

**Impact**: 10-100x faster queries on filtered columns

---

### 3.2 Text Search Not Optimized
**Issue**: Name/email searches use LIKE which doesn't use indexes

**Example**:
```sql
-- Slow query (doesn't use index)
SELECT * FROM team_members WHERE name LIKE '%John%';
```

**Fix**: Add full-text search indexes
```sql
-- Migration: 016_add_fulltext_search.sql

-- Add tsvector columns for full-text search
ALTER TABLE team_members 
ADD COLUMN search_vector tsvector 
GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(email, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(bio, '')), 'C')
) STORED;

CREATE INDEX idx_team_members_search 
ON team_members USING GIN(search_vector);

-- Search function
CREATE OR REPLACE FUNCTION search_team_members(search_query TEXT)
RETURNS TABLE (
    member_id UUID,
    member_name VARCHAR(255),
    member_email VARCHAR(255),
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        id,
        name,
        email,
        ts_rank(search_vector, websearch_to_tsquery('english', search_query)) as rank
    FROM team_members
    WHERE search_vector @@ websearch_to_tsquery('english', search_query)
    AND status = 'active'
    ORDER BY rank DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql STABLE;

-- Usage:
-- SELECT * FROM search_team_members('John Doe');
```

---

### 3.3 No Query Performance Monitoring
**Issue**: No visibility into slow queries

**Fix**: Enable pg_stat_statements
```sql
-- In Supabase dashboard: Database > Extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slow queries
CREATE OR REPLACE VIEW slow_queries AS
SELECT
    substring(query, 1, 100) as short_query,
    round(total_exec_time::numeric, 2) as total_time_ms,
    calls,
    round(mean_exec_time::numeric, 2) as avg_time_ms,
    round((100 * total_exec_time / sum(total_exec_time) OVER ())::numeric, 2) as pct_total
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Reset stats periodically
-- SELECT pg_stat_statements_reset();
```

---

### 3.4 Large Tables Not Partitioned
**Issue**: `audit_log` and `pending_onboarding` will grow indefinitely

**Risk**: Medium - Slow queries after ~1M rows

**Fix**: Add partitioning for large tables
```sql
-- Migration: 017_partition_large_tables.sql

-- Partition audit_log by month
CREATE TABLE audit_log_partitioned (
    LIKE audit_log INCLUDING ALL
) PARTITION BY RANGE (changed_at);

-- Create partitions for current and next 6 months
CREATE TABLE audit_log_2024_12 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');
    
CREATE TABLE audit_log_2025_01 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- ... create more partitions

-- Function to auto-create next month's partition
CREATE OR REPLACE FUNCTION create_next_audit_partition()
RETURNS void AS $$
DECLARE
    next_month DATE := date_trunc('month', NOW() + INTERVAL '1 month');
    month_after DATE := next_month + INTERVAL '1 month';
    partition_name TEXT := 'audit_log_' || to_char(next_month, 'YYYY_MM');
BEGIN
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_log_partitioned
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, next_month, month_after
    );
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly (with pg_cron or external cron)
-- SELECT cron.schedule('create-audit-partition', '0 0 1 * *', 'SELECT create_next_audit_partition()');
```

---

## 4. Data Quality & Consistency 🟡 MEDIUM

### 4.1 No Unique Constraint on Discord Username + Discriminator
**Table**: `team_members.discord_username`
**Issue**: `discord_username` is UNIQUE but should be composite with discriminator

**Context**: Discord usernames can be duplicated (different discriminators)

**Fix**: Change discord_username to store full username#discriminator
```sql
-- Migration: 018_fix_discord_username.sql

-- Remove old unique constraint
ALTER TABLE team_members DROP CONSTRAINT IF EXISTS team_members_discord_username_key;

-- Update column to store full username (username#0 for new format, username#1234 for old)
-- No constraint needed since discord_id is already unique
COMMENT ON COLUMN team_members.discord_username IS 'Discord username (username#discriminator or username for new format)';
```

---

### 4.2 Status Enum Values Inconsistent
**Issue**: Different tables use different status values

**Examples**:
- `team_members.status`: 'active', 'inactive', 'pending'
- `pending_onboarding.status`: 'pending', 'approved', 'rejected'

**Fix**: Create reusable ENUMs
```sql
-- Migration: 019_create_enums.sql

-- Create custom types
CREATE TYPE member_status AS ENUM ('active', 'inactive', 'pending', 'suspended');
CREATE TYPE onboarding_status AS ENUM ('pending', 'approved', 'rejected', 'expired');
CREATE TYPE team_role_level AS ENUM ('individual', 'lead', 'manager', 'director', 'executive');

-- Migrate existing columns (requires data migration)
ALTER TABLE team_members 
ALTER COLUMN status TYPE member_status USING status::member_status;

ALTER TABLE pending_onboarding 
ALTER COLUMN status TYPE onboarding_status USING status::onboarding_status;

-- Benefits:
-- 1. Type safety - prevents invalid values
-- 2. Better performance - stored as integers internally
-- 3. Self-documenting - show valid values in schema
```

---

### 4.3 Timestamps Missing Timezone
**Issue**: All timestamps are `TIMESTAMP` not `TIMESTAMPTZ`

**Risk**: Low - But causes confusion across timezones

**Fix**: Migrate to TIMESTAMPTZ
```sql
-- Migration: 020_add_timezone_to_timestamps.sql

-- Update all timestamp columns
ALTER TABLE team_members 
ALTER COLUMN created_at TYPE TIMESTAMPTZ,
ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

ALTER TABLE teams 
ALTER COLUMN created_at TYPE TIMESTAMPTZ,
ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- ... repeat for all tables

-- Set default timezone
ALTER DATABASE postgres SET timezone TO 'UTC';
```

---

### 4.4 No Default Values for Common Fields
**Issue**: Missing sensible defaults

**Examples**:
- `teams.created_at` has DEFAULT NOW() ✅
- `teams.updated_at` has DEFAULT NOW() but not updated on UPDATE ❌
- `team_memberships.joined_at` has DEFAULT NOW() ✅

**Fix**: Add UPDATE triggers for updated_at
```sql
-- Generic trigger function (should exist)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_team_members_updated_at
    BEFORE UPDATE ON team_members
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_team_memberships_updated_at
    BEFORE UPDATE ON team_memberships
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add to clickup_lists (already has trigger function)
CREATE TRIGGER update_clickup_lists_updated_at
    BEFORE UPDATE ON clickup_lists
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## 5. Schema Design Issues 🟡 MEDIUM

### 5.1 team_members.team is Denormalized
**Issue**: `team_members.team` (VARCHAR) duplicates `team_memberships` relationship

**Problems**:
- Can be out of sync with team_memberships
- Doesn't support multiple team memberships
- Harder to maintain

**Fix**: Remove denormalized column, use team_memberships
```sql
-- Migration: 021_remove_denormalized_team.sql

-- Verify all team values exist in team_memberships
-- If not, create missing memberships
INSERT INTO team_memberships (team_id, member_id, role, is_active)
SELECT 
    t.id,
    tm.id,
    'Team Member',
    true
FROM team_members tm
INNER JOIN teams t ON t.name = tm.team
WHERE tm.team IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM team_memberships tms 
    WHERE tms.member_id = tm.id AND tms.team_id = t.id
);

-- Drop the denormalized column
ALTER TABLE team_members DROP COLUMN team;

-- Create view for backwards compatibility
CREATE OR REPLACE VIEW team_members_with_team AS
SELECT 
    tm.*,
    t.name as primary_team
FROM team_members tm
LEFT JOIN LATERAL (
    SELECT teams.name
    FROM team_memberships tms
    INNER JOIN teams ON teams.id = tms.team_id
    WHERE tms.member_id = tm.id
    AND tms.is_active = true
    ORDER BY tms.joined_at ASC
    LIMIT 1
) t ON true;

-- Application code should use:
-- SELECT * FROM team_members_with_team WHERE primary_team = 'Engineering';
```

---

### 5.2 team_members.role is String not FK
**Issue**: `role` is VARCHAR(50) instead of FK to roles table

**Problems**:
- Typos possible ("Manger" vs "Manager")
- No referential integrity
- Hard to enforce permissions

**Fix**: Add FK constraint
```sql
-- Migration: 022_add_role_fk.sql

-- First, clean up any invalid roles
UPDATE team_members 
SET role = 'Individual Contributor' 
WHERE role NOT IN (SELECT name FROM roles);

-- Add FK constraint
ALTER TABLE team_members 
DROP CONSTRAINT IF EXISTS team_members_role_fkey,
ADD CONSTRAINT team_members_role_fkey 
FOREIGN KEY (role) REFERENCES roles(name) ON DELETE RESTRICT;

-- Same for pending_onboarding
UPDATE pending_onboarding 
SET role = 'Individual Contributor' 
WHERE role NOT IN (SELECT name FROM roles) AND role IS NOT NULL;

ALTER TABLE pending_onboarding 
ADD CONSTRAINT pending_onboarding_role_fkey 
FOREIGN KEY (role) REFERENCES roles(name) ON DELETE RESTRICT;
```

---

### 5.3 Clickup Integration Data Scattered
**Issue**: ClickUp data split across multiple tables
- `team_members.clickup_api_token` - User tokens
- `teams.clickup_workspace_id`, `teams.clickup_space_id` - Team workspaces
- `clickup_lists` - Lists
- `project_brainstorms.clickup_list_id` - List references

**Better Design**: Centralize ClickUp data
```sql
-- Migration: 023_centralize_clickup_data.sql

-- New table for ClickUp integration metadata
CREATE TABLE clickup_integration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    workspace_id VARCHAR(100),
    workspace_name VARCHAR(255),
    space_id VARCHAR(100),
    space_name VARCHAR(255),
    sync_enabled BOOLEAN DEFAULT true,
    last_synced_at TIMESTAMPTZ,
    sync_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id)
);

-- Migrate existing data
INSERT INTO clickup_integration (team_id, workspace_id, space_id)
SELECT id, clickup_workspace_id, clickup_space_id
FROM teams
WHERE clickup_workspace_id IS NOT NULL OR clickup_space_id IS NOT NULL;

-- Remove from teams table
ALTER TABLE teams 
DROP COLUMN clickup_workspace_id,
DROP COLUMN clickup_space_id,
DROP COLUMN clickup_workspace_name;

-- User tokens table (separate from team_members)
CREATE TABLE clickup_user_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID UNIQUE NOT NULL REFERENCES team_members(id) ON DELETE CASCADE,
    encrypted_token TEXT NOT NULL,  -- Use encryption
    clickup_user_id VARCHAR(100),
    clickup_username VARCHAR(255),
    token_valid BOOLEAN DEFAULT true,
    last_validated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Migrate tokens (after implementing encryption)
-- INSERT INTO clickup_user_tokens (member_id, encrypted_token, clickup_user_id)
-- SELECT id, encrypt(clickup_api_token), clickup_user_id
-- FROM team_members
-- WHERE clickup_api_token IS NOT NULL;

-- ALTER TABLE team_members DROP COLUMN clickup_api_token;
```

---

## 6. Migration Management 🟠 HIGH

### 6.1 No Migration Tracking Table
**Issue**: Migrations applied manually, no tracking of what's been run

**Risk**: Medium - Can accidentally re-run migrations or miss some

**Fix**: Add migrations tracking table
```sql
-- Migration: 001_create_migrations_table.sql (should be first)

CREATE TABLE schema_migrations (
    version VARCHAR(14) PRIMARY KEY,  -- YYYYMMDDHHMMSS format
    name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    checksum VARCHAR(64),  -- SHA256 of migration file
    execution_time_ms INTEGER,
    applied_by VARCHAR(255) DEFAULT current_user,
    description TEXT
);

COMMENT ON TABLE schema_migrations IS 'Tracks which database migrations have been applied';

-- Index for quick lookups
CREATE INDEX idx_schema_migrations_applied ON schema_migrations(applied_at DESC);

-- Function to record migration
CREATE OR REPLACE FUNCTION record_migration(
    version_param VARCHAR(14),
    name_param VARCHAR(255),
    description_param TEXT DEFAULT NULL
)
RETURNS void AS $$
BEGIN
    INSERT INTO schema_migrations (version, name, description)
    VALUES (version_param, name_param, description_param)
    ON CONFLICT (version) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- Usage in each migration:
-- SELECT record_migration('20241214000001', '001_create_migrations_table', 'Initial migration tracking');
```

**Tool**: Create migration runner script
```python
# scripts/run_migrations.py
import os
import hashlib
from pathlib import Path
from supabase import create_client

def get_applied_migrations(client):
    """Get list of applied migrations."""
    result = client.table('schema_migrations').select('version').execute()
    return {row['version'] for row in result.data}

def get_migration_checksum(file_path):
    """Calculate SHA256 checksum of migration file."""
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def run_migration(client, file_path):
    """Run a single migration file."""
    version = file_path.stem.split('_')[0]
    name = file_path.stem
    checksum = get_migration_checksum(file_path)
    
    with open(file_path) as f:
        sql = f.read()
    
    # Execute migration
    import time
    start = time.time()
    client.postgrest.rpc('exec_sql', {'sql': sql}).execute()
    execution_time = int((time.time() - start) * 1000)
    
    # Record migration
    client.table('schema_migrations').insert({
        'version': version,
        'name': name,
        'checksum': checksum,
        'execution_time_ms': execution_time
    }).execute()
    
    print(f"✅ Applied {name} ({execution_time}ms)")

def main():
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
    migrations_dir = Path('shared-services/database/migrations')
    
    applied = get_applied_migrations(client)
    pending = sorted([
        f for f in migrations_dir.glob('*.sql')
        if f.stem.split('_')[0] not in applied
    ])
    
    if not pending:
        print("✅ All migrations applied")
        return
    
    print(f"📋 Found {len(pending)} pending migrations")
    for migration in pending:
        run_migration(client, migration)
    
    print(f"✅ Applied {len(pending)} migrations")

if __name__ == '__main__':
    main()
```

---

### 6.2 Migration Naming Inconsistent
**Issue**: Migrations use different naming conventions
- `000_complete_schema.sql` - No timestamp
- `001_create_team_members.sql` - Sequential number
- `009_simplify_team_members_schema.sql` - Sequential

**Best Practice**: Use timestamp-based versioning

**Fix**: Rename to YYYYMMDDHHMMSS_description.sql
```
Current:                     Recommended:
000_complete_schema.sql  →  20241201000000_complete_schema.sql
001_initial_schema.sql   →  20241201000001_initial_schema.sql
002_add_teams.sql        →  20241202000000_add_teams.sql
...
010_add_manager_role.sql →  20241214000000_add_manager_role.sql
```

**Benefits**:
- Sortable by timestamp
- Handles concurrent development (different timestamps)
- Easier to track when migration was created

---

## 7. Backup & Recovery 🟠 HIGH

### 7.1 No Point-in-Time Recovery Testing
**Issue**: Supabase has PITR but not tested

**Recommendation**: Test backup/restore procedure
```sql
-- Create test restore procedure
-- 1. Take snapshot before changes
-- 2. Make test changes
-- 3. Restore to snapshot
-- 4. Verify data restored correctly

-- Document in README
```

---

### 7.2 No Data Retention Policy
**Issue**: Soft deletes not implemented

**Fix**: Add soft delete columns
```sql
-- Migration: 024_add_soft_deletes.sql

-- Add deleted_at column to main tables
ALTER TABLE team_members ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE teams ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE team_memberships ADD COLUMN deleted_at TIMESTAMPTZ;

-- Create indexes for non-deleted records
CREATE INDEX idx_team_members_not_deleted 
ON team_members(id) WHERE deleted_at IS NULL;

CREATE INDEX idx_teams_not_deleted 
ON teams(id) WHERE deleted_at IS NULL;

-- Update queries to filter deleted records
-- SELECT * FROM team_members WHERE deleted_at IS NULL;

-- Soft delete function
CREATE OR REPLACE FUNCTION soft_delete_team_member(member_id_param UUID)
RETURNS void AS $$
BEGIN
    UPDATE team_members SET deleted_at = NOW() WHERE id = member_id_param;
    UPDATE team_memberships SET deleted_at = NOW() WHERE member_id = member_id_param;
END;
$$ LANGUAGE plpgsql;

-- Hard delete after 90 days
CREATE OR REPLACE FUNCTION cleanup_soft_deleted()
RETURNS void AS $$
BEGIN
    DELETE FROM team_members WHERE deleted_at < NOW() - INTERVAL '90 days';
    DELETE FROM teams WHERE deleted_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;
```

---

## 8. Documentation & Maintenance 🟡 MEDIUM

### 8.1 Missing Table/Column Comments
**Issue**: Schema lacks documentation

**Fix**: Add comprehensive comments
```sql
-- Migration: 025_add_schema_documentation.sql

-- Table comments
COMMENT ON TABLE team_members IS 'Core user profiles with authentication and role information';
COMMENT ON TABLE teams IS 'Organizational teams with hierarchy and external integrations';
COMMENT ON TABLE team_memberships IS 'Many-to-many relationship between teams and members';
COMMENT ON TABLE roles IS 'Permission levels and role definitions';
COMMENT ON TABLE pending_onboarding IS 'Onboarding requests awaiting admin approval';
COMMENT ON TABLE clickup_lists IS 'ClickUp lists configured for each team';
COMMENT ON TABLE project_brainstorms IS 'AI-generated project plans from /brainstorm command';

-- Column comments (examples)
COMMENT ON COLUMN team_members.user_id IS 'Reference to Supabase auth.users - used for authentication';
COMMENT ON COLUMN team_members.discord_id IS 'Discord user ID (snowflake) - primary identifier from Discord';
COMMENT ON COLUMN team_members.clickup_api_token IS 'Encrypted ClickUp API token for task management integration';
COMMENT ON COLUMN teams.team_lead_id IS 'Reference to team member who leads this team';
COMMENT ON COLUMN teams.parent_team_id IS 'Reference to parent team for hierarchical structure';
```

---

### 8.2 No ER Diagram
**Issue**: No visual representation of schema

**Recommendation**: Generate ER diagram
```bash
# Using SchemaSpy
docker run -v "$PWD:/output" schemaspy/schemaspy:latest \
    -t pgsql \
    -host $DB_HOST \
    -db $DB_NAME \
    -u $DB_USER \
    -p $DB_PASSWORD \
    -o /output

# Or using dbdiagram.io
# Export schema and paste into https://dbdiagram.io/
```

---

## 9. Monitoring & Observability 🟢 LOW

### 9.1 No Table Size Monitoring
**Fix**: Create monitoring views
```sql
-- View table sizes
CREATE OR REPLACE VIEW table_sizes AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;

-- View index usage
CREATE OR REPLACE VIEW index_usage AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- Unused indexes
CREATE OR REPLACE VIEW unused_indexes AS
SELECT * FROM index_usage WHERE index_scans = 0;
```

---

## Implementation Roadmap

### Phase 1: Critical Security (Day 1-2)
**Must complete before production**

1. ✅ Add audit logging (1.3)
2. ✅ Fix NOT NULL constraints (2.1)
3. ✅ Fix CASCADE deletes (2.4)
4. ✅ Add migration tracking (6.1)
5. ✅ Test backup/restore (7.1)

### Phase 2: Performance (Day 3-4)
**Complete in first week**

1. ✅ Add composite indexes (3.1)
2. ✅ Add full-text search (3.2)
3. ✅ Enable pg_stat_statements (3.3)
4. ✅ Fix role FK constraint (5.2)
5. ✅ Add soft deletes (7.2)

### Phase 3: Data Quality (Week 2)
**Complete in first month**

1. ✅ Add email validation (2.2)
2. ✅ Add phone validation (2.3)
3. ✅ Create ENUMs (4.2)
4. ✅ Fix timestamp timezones (4.3)
5. ✅ Add schema documentation (8.1)

### Phase 4: Advanced (Ongoing)
**Nice to have improvements**

1. ✅ Encrypt sensitive data (1.2)
2. ✅ Partition large tables (3.4)
3. ✅ Refactor ClickUp schema (5.3)
4. ✅ Generate ER diagram (8.2)
5. ✅ Add monitoring views (9.1)

---

## Quick Wins (< 30 minutes each)

1. **Add table comments** - Document purpose of tables/columns
2. **Enable pg_stat_statements** - See slow queries
3. **Create table_sizes view** - Monitor growth
4. **Fix phone validation** - Add CHECK constraint
5. **Add updated_at triggers** - Auto-update timestamps

---

## Estimated Impact

### Current State
- **Query Performance**: Slow on filtered queries (no composite indexes)
- **Data Integrity**: Medium risk (weak constraints, orphans possible)
- **Security**: Medium risk (no audit log, plaintext tokens)
- **Maintainability**: Low (no migration tracking, poor docs)

### After Phase 1 (Critical)
- **Query Performance**: Same
- **Data Integrity**: High (strong constraints, cascades fixed)
- **Security**: High (audit log, no orphans)
- **Maintainability**: Medium (migration tracking)

### After All Phases
- **Query Performance**: Excellent (10-100x faster on common queries)
- **Data Integrity**: Excellent (ENUMs, validation, FKs)
- **Security**: Excellent (encryption, audit log, monitoring)
- **Maintainability**: Excellent (docs, tracking, monitoring)

---

## Files to Create

```
shared-services/database/
├── migrations/
│   ├── 011_encrypt_sensitive_data.sql
│   ├── 012_add_audit_logging.sql
│   ├── 013_add_not_null_constraints.sql
│   ├── 014_fix_cascade_deletes.sql
│   ├── 015_add_composite_indexes.sql
│   ├── 016_add_fulltext_search.sql
│   ├── 017_partition_large_tables.sql
│   ├── 018_fix_discord_username.sql
│   ├── 019_create_enums.sql
│   ├── 020_add_timezone_to_timestamps.sql
│   ├── 021_remove_denormalized_team.sql
│   ├── 022_add_role_fk.sql
│   ├── 023_centralize_clickup_data.sql
│   ├── 024_add_soft_deletes.sql
│   └── 025_add_schema_documentation.sql
├── scripts/
│   ├── run_migrations.py      # NEW: Migration runner
│   ├── verify_schema.py       # NEW: Schema validation
│   └── generate_er_diagram.sh # NEW: ER diagram generator
└── docs/
    ├── schema.md              # NEW: Schema documentation
    └── er_diagram.png         # NEW: Visual schema

```

---

**Document Status**: Ready for Implementation  
**Priority**: Complete Phase 1 before production deployment  
**Estimated Total Effort**: 5-7 days for all improvements

