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
- `POST /brainstorm` - Generate project plan from idea
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

FastAPI service that:
1. Accepts HTTP requests from Discord bot
2. Calls Claude AI for project analysis
3. Creates formatted Google Docs
4. Saves to Supabase database

See `../PROJECT_PLANNING_ARCHITECTURE.md` for full details.
