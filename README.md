# Alfred

Digital butler to help run distributed teams through automation and integrations.

## Components

### discord-bot
Discord-first onboarding system with admin approval, automated Google Docs profile creation, and role assignment. Includes ClickUp task management integration.

### team-management-system
Automated ClickUp project setup with AI-powered task assignment based on team member skills and availability.

### shared-services
Reusable services for Supabase database access, Google Docs/Drive integration, and authentication used across all Alfred components.

## Setup

Each component has its own setup instructions. See individual README files:
- `discord-bot/README.md`
- `team-management-system/README.md`
- `shared-services/*/README.md`

## Quick Start

### Discord Bot (Primary Onboarding System)
```bash
cd discord-bot
source .venv/bin/activate
uv pip install -e .
cp .env.example .env
# Configure .env with Discord tokens and Supabase credentials
python create_admin.py  # First-time admin setup
./run.sh
```

### Team Management
```bash
cd team-management-system
uv run setup-project --preview  # Preview project structure
uv run setup-project            # Create in ClickUp
```

See `progress.md` for detailed documentation and deployment guides.
