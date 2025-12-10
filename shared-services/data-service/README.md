# Data Service

Centralized data models and database operations for the Alfred system.

## Purpose

This service provides:
- Pydantic models for all database entities
- CRUD operations for team members
- Database-agnostic interface (currently Supabase, easy to migrate to PostgreSQL)

## Models

### TeamMember
Core model for team member data:
- Profile info (name, email, bio)
- Integration identifiers (Discord username, ClickUp user ID)
- Skills and preferences
- Availability and timezone
- Profile document links

### Supporting Models
- `Skill` - Skill with experience level
- `ExperienceLevel` - Enum for skill levels
- `TeamMemberCreate` - For creating new members
- `TeamMemberUpdate` - For updating existing members

## Usage

```python
from data_service import create_data_service, TeamMemberCreate, Skill, ExperienceLevel

# Initialize service
data = create_data_service()

# Create a team member
member = TeamMemberCreate(
    user_id=user_uuid,
    email="alice@example.com",
    name="Alice Smith",
    discord_username="alice#1234",
    skills=[
        Skill(name="Python", experience_level=ExperienceLevel.EXPERT, years_of_experience=5),
        Skill(name="FastAPI", experience_level=ExperienceLevel.ADVANCED, years_of_experience=3),
    ],
    availability_hours=40,
    timezone="America/New_York",
)

created = data.create_team_member(member)
print(f"Created: {created.id}")

# Get member by Discord username (for bot)
member = data.get_team_member_by_discord("alice#1234")
print(f"ClickUp ID: {member.clickup_user_id}")

# List all members
members = data.list_team_members()
for m in members:
    print(f"{m.name} - {len(m.skills)} skills")

# Update member
from data_service import TeamMemberUpdate

updates = TeamMemberUpdate(
    clickup_user_id="12345",
    availability_hours=30,
)
updated = data.update_team_member(member.id, updates)

# Find members with specific skill
python_devs = data.get_members_with_skill("Python")
```

## Environment Variables

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

## Database Schema

See `../database/migrations/001_create_team_members.sql` for the full schema.

## Migration to PostgreSQL

When migrating to self-hosted PostgreSQL:

1. Update `client.py` to use `psycopg2` or `asyncpg` instead of Supabase client
2. Keep the same models and interface
3. All calling code remains unchanged

Example:
```python
# Future PostgreSQL implementation
class DataService:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        # Same methods, different implementation
```

## Used By

- **onboarding-app** - Creates team members during onboarding
- **discord-bot** (future) - Looks up members by Discord username
- **team-management-system** (future) - Reads member data for task assignment
- **admin-tools** (future) - Manages team members

## Design Principles

1. **Database-agnostic**: Models use standard Pydantic, easy to swap backends
2. **Type-safe**: Full type hints for IDE support
3. **Validation**: Pydantic handles all input validation
4. **Reusable**: Single source of truth for team data
5. **Migration-ready**: Easy to move from Supabase to PostgreSQL
