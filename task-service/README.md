# Task Service

Platform-agnostic task management service for ClickUp operations.

## Quick Start

```bash
# Install dependencies
uv pip install -e .

# Copy and configure .env
cp .env.example .env

# Start service
uvicorn api.app:app --host 0.0.0.0 --port 8002
```

## API Endpoints

- `GET /health` - Health check
- `GET /tasks/user/{discord_user_id}` - Get user's tasks
- `GET /tasks/{task_id}` - Get task details
- `GET /tasks/{task_id}/comments` - Get task comments
- `POST /tasks/{task_id}/comment` - Add comment to task

## Architecture

Extracts ClickUp operations from Discord bot to be platform-agnostic.
Can be used by Discord bot, Slack bot, web app, etc.
