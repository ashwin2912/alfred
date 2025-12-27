# Database Setup

## Overview
Alfred uses Supabase (PostgreSQL) for data storage and authentication.

---

## Required Tables

### Teams Table
```sql
CREATE TABLE teams (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  drive_folder_id TEXT,
  discord_general_channel_id BIGINT,
  discord_standup_channel_id BIGINT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Team Members Table
```sql
CREATE TABLE team_members (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  discord_id TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  team TEXT,
  role TEXT,
  clickup_api_token TEXT,
  supabase_user_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Project Lists Table
```sql
CREATE TABLE project_lists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  team_name TEXT NOT NULL,
  clickup_list_id TEXT NOT NULL,
  list_name TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Setup Instructions

### Option 1: Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard
2. Click "SQL Editor" in the sidebar
3. Click "New Query"
4. Copy and paste all three CREATE TABLE statements above
5. Click "Run"

### Option 2: Using Migrations

If you have database migrations in `shared-services/database/migrations/`:

```bash
# Apply migrations
cd shared-services/database
python apply_migrations.py
```

### Option 3: Via API

```python
from data_service.client import create_data_service

# Initialize client
data_service = create_data_service(
    supabase_url="your-url",
    supabase_key="your-key"
)

# Tables are auto-created on first use (if using ORM)
# Or run raw SQL:
data_service.client.rpc('exec', {'sql': 'CREATE TABLE ...'})
```

---

## Verify Setup

```python
from supabase import create_client

client = create_client("your-url", "your-key")

# Check tables exist
tables = client.table('teams').select('*').limit(1).execute()
print("✅ Teams table exists" if tables else "❌ Teams table missing")
```

Or via SQL:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

Should show: `teams`, `team_members`, `project_lists`

---

## Initial Data

### Create Your First Team

```sql
INSERT INTO teams (name, discord_general_channel_id, discord_standup_channel_id)
VALUES ('Engineering', 123456789, 987654321);
```

Or via Discord:
```
/create-team
```

---

## Data Integrity (Optional)

For production, add constraints:

```sql
-- Email validation
ALTER TABLE team_members 
ADD CONSTRAINT valid_email 
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Phone validation (if you add phone field)
ALTER TABLE team_members 
ADD CONSTRAINT valid_phone 
CHECK (phone ~ '^\+?[1-9]\d{1,14}$');

-- Cascade deletes
ALTER TABLE project_lists
ADD CONSTRAINT fk_team
FOREIGN KEY (team_name) REFERENCES teams(name)
ON DELETE CASCADE;
```

---

## Backup

```bash
# Export data
supabase db dump > backup.sql

# Or via pg_dump
pg_dump -h your-db-url -U postgres -d your-db > backup.sql
```

---

## Troubleshooting

**Permission denied:**
```
Error: permission denied for table teams
```
→ Use service role key, not anon key

**Table already exists:**
```
Error: relation "teams" already exists
```
→ Tables are already set up, skip creation

**Connection failed:**
```
Error: could not connect to server
```
→ Check `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env`

---

## Next Steps

- [Setup Discord Bot](../README.md#quick-start)
- [Deploy to Production](MANUAL_DEPLOYMENT.md)
- [Configure CI/CD](CI_CD_SETUP.md)
