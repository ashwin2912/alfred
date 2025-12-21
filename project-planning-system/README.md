# Project Planning API

AI-powered project planning service using Claude Haiku 4.5.

## Quick Start

### First Time Setup

```bash
# 1. Run setup script
./setup.sh

# 2. Edit .env with your keys
nano .env

# 3. Start the server
./run.sh
```

### Daily Use

```bash
./run.sh
```

Server runs on `http://localhost:8001`

## API Endpoints

- `GET /health` - Health check
- `POST /brainstorm` - Generate AI project breakdown and Google Doc
- `POST /publish-project` - Publish project plan to ClickUp
- `GET /projects/{discord_user_id}` - List user's projects
- `GET /projects/detail/{brainstorm_id}` - Get project details

## Configuration

Required environment variables in `.env`:

```bash
ANTHROPIC_API_KEY=your_key_here
GOOGLE_CREDENTIALS_PATH=/path/to/service-account.json
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
```

## Architecture

FastAPI microservice that:
1. Accepts HTTP requests from Discord bot
2. Calls Claude Haiku 4.5 for project breakdown (JSON output)
3. Creates "Plan" Google Docs with editing instructions
4. Publishes to ClickUp with hierarchical structure:
   - Phases as parent tasks
   - Subtasks under phases
   - All tagged with project title
5. Saves structured data to Supabase

## Key Features

- **No Time Estimates**: Plans focus on structure, not duration
- **Hierarchical Tasks**: Phases → Subtasks in ClickUp
- **Editable Plans**: Google Docs with clear editing instructions
- **Multi-List Support**: Teams can configure multiple ClickUp lists
- **Permission-Based**: Channel manager access required

See `../PROJECT_PLANNING_ARCHITECTURE.md` for full details.
