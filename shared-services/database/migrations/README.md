# Database Migrations

## Running Migrations

### Option 1: Supabase Dashboard (Recommended)

1. Go to your Supabase project: https://supabase.com/dashboard
2. Navigate to **SQL Editor**
3. Click **New Query**
4. Copy the contents of `001_create_team_members.sql`
5. Paste into the editor
6. Click **Run** (or press Cmd+Enter)
7. Verify success message

### Option 2: Supabase CLI

```bash
# Install Supabase CLI if not already installed
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref ipjlwuwaciiyucwdcqvh

# Run migration
supabase db push --file migrations/001_create_team_members.sql
```

### Option 3: psql (Direct Connection)

```bash
# Get connection string from Supabase dashboard
# Settings -> Database -> Connection string (Direct connection)

psql "postgresql://postgres:[PASSWORD]@db.ipjlwuwaciiyucwdcqvh.supabase.co:5432/postgres" \
  -f migrations/001_create_team_members.sql
```

---

## Verification

After running the migration, verify it worked:

```sql
-- Check table exists
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'team_members';

-- Check columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'team_members'
ORDER BY ordinal_position;

-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'team_members';

-- Check RLS policies
SELECT policyname, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'team_members';
```

---

## Rollback (if needed)

If you need to undo this migration:

```sql
-- Drop table and all related objects
DROP TABLE IF EXISTS public.team_members CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;
```

---

## What This Migration Creates

### Table: `team_members`

**Core Fields**:
- `id` - UUID primary key
- `user_id` - Links to Supabase auth.users
- `email` - Unique email address
- `name` - Team member name

**Integration Fields**:
- `discord_username` - For Discord bot (unique)
- `clickup_user_id` - ClickUp user identifier
- `clickup_api_token` - Optional personal token

**Profile Fields**:
- `bio` - Short bio
- `timezone` - User timezone
- `availability_hours` - Hours per week
- `skills` - JSONB array of skill objects
- `preferred_tasks` - JSONB array of task preferences
- `links` - JSONB object with external links

**Document Fields**:
- `profile_doc_id` - Google Docs document ID
- `profile_url` - Public URL to profile doc

**Timestamps**:
- `onboarded_at` - When user completed onboarding
- `created_at` - Record creation time
- `updated_at` - Last update time (auto-updated)

### Indexes

- `idx_team_members_user_id` - Fast auth user lookups
- `idx_team_members_email` - Fast email searches
- `idx_team_members_discord_username` - Discord bot lookups
- `idx_team_members_clickup_user_id` - ClickUp integration

### Row Level Security (RLS)

**Policies**:
1. Authenticated users can view all team members
2. Users can update their own profile
3. Service role can insert new members
4. Service role can update any member
5. Service role can delete members

This ensures:
- Discord bot can lookup any user
- Users can self-manage their profile
- Onboarding app (using service key) can create users
- Admins (using service key) have full control

---

## Next Steps

After running this migration:

1. Create Pydantic models in `auth_service/models.py`
2. Add CRUD functions in `auth_service/supabase_client.py`
3. Update onboarding API to insert into `team_members`
4. Add Discord username field to Streamlit form
5. Create API endpoints for team management
