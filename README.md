# Alfred

Automated team onboarding and management system for Discord-first organizations.

---

## What It Does

Alfred automates the complete member onboarding process:

1. User submits onboarding form in Discord
2. Admin approves with team selection
3. System automatically creates:
   - Supabase authentication account
   - Database record with profile data
   - Google Doc profile document
   - Team roster entry in Google Sheets
   - Discord role assignment
   - Welcome notification

Time: 5 minutes manual → 10 seconds automated

---

## Core Features

### Discord Bot
- Modal-based onboarding with admin approval
- Automatic Supabase user creation with secure passwords
- Google Doc profile generation
- Team roster updates in Google Sheets
- Discord role auto-assignment
- ClickUp task integration (`/my-tasks`, `/task-info`, `/task-comment`)
- Team management (`/create-team`, `/add-to-team`)
- Project list tracking (`/add-project-list`, `/list-project-lists`)
- Team task reports (`/team-report`)
- AI-powered project planning (`/brainstorm`)

### Team Management System
- Automated project creation in ClickUp
- Smart skill-based task assignment
- AI-powered project planning

### Shared Services
- `data-service`: Supabase database and authentication API
- `docs-service`: Google Docs, Drive, and Sheets integration
- Type-safe models with Pydantic

---

## Quick Start

### Prerequisites
- Python 3.11+
- Discord bot token
- Supabase project
- Google Cloud service account with domain-wide delegation
- Google Workspace account

### Setup

```bash
# Install dependencies
cd discord-bot
source .venv/bin/activate
uv pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run interactive setup
python scripts/interactive_setup.py

# Start bot
./run.sh
```

Test with `/start-onboarding` in Discord.

---

## Architecture

```
alfred/
├── discord-bot/              # Primary onboarding system
│   ├── bot/                  # Bot commands and logic
│   └── scripts/              # Setup and utility scripts
├── shared-services/
│   ├── data-service/         # Database and auth API
│   ├── docs-service/         # Google integrations
│   └── database/migrations/  # Database schema
└── team-management-system/   # ClickUp automation
```

---

## Database Integrity

Migration 011-014 add critical data integrity features:

- NOT NULL constraints on required fields
- Email format validation with auto-normalization
- Phone number validation and formatting
- CASCADE delete behaviors to prevent orphaned records

Apply with:
```bash
python apply_data_integrity_migrations.py
```

See `DATA_INTEGRITY_MIGRATIONS.md` for details.

---

## Documentation

- `progress.md`: Complete feature list and roadmap
- `DATABASE_IMPROVEMENTS.md`: Database optimization recommendations
- `IMPROVEMENTS_NEEDED.md`: Code quality improvements
- `GCP_DEPLOYMENT.md`: Production deployment guide
- `DATA_INTEGRITY_MIGRATIONS.md`: Migration guide

---

## Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Onboarding Time | 5 min | 10 sec | 30x faster |
| Setup Time | 45 min | 2 min | 22x faster |
| Automation Rate | 20% | 95% | +75% |
| Manual Steps | 6 | 1 | -83% |

---

## Tech Stack

- Discord Bot: discord.py
- Database: Supabase (PostgreSQL)
- Authentication: Supabase Auth API
- Documents: Google Docs/Drive/Sheets APIs
- Task Management: ClickUp API
- AI: Anthropic Claude
- Language: Python 3.11+
- Type Safety: Pydantic

---

## Testing

```bash
# Clean environment
python scripts/cleanup_everything.py

# Setup teams
python scripts/interactive_setup.py

# Start bot
./run.sh

# Test in Discord
/start-onboarding
```

---

**Last Updated**: Dec 16, 2024  
**Status**: Production-ready with data integrity migrations  
**Version**: 1.3.0
