# Project Planning System - Architecture

## ✅ Refactored to Microservices

The Project Planning System is now a **separate FastAPI service** that the Discord bot calls via HTTP.

---

## 🏗️ Architecture Overview

```
┌─────────────────────┐
│   Discord Bot       │
│  (Port: Discord)    │
│                     │
│  Commands:          │
│  - /brainstorm      │
│  - /my-projects     │
└──────────┬──────────┘
           │
           │ HTTP POST/GET
           │
           ▼
┌─────────────────────┐
│  Planning API       │
│  (Port: 8001)       │
│                     │
│  Endpoints:         │
│  - POST /brainstorm │
│  - GET /projects    │
│  - GET /health      │
└──────────┬──────────┘
           │
           ├─────────────────────┐
           │                     │
           ▼                     ▼
┌──────────────────┐   ┌──────────────────┐
│  Anthropic API   │   │  Google Docs API │
│  (Claude Haiku)  │   │  (Doc Creation)  │
└──────────────────┘   └──────────────────┘
           │
           ▼
┌──────────────────┐
│  Supabase DB     │
│  (project_       │
│   brainstorms)   │
└──────────────────┘
```

---

## 📦 Components

### 1. **Project Planning API** (Port 8001)
**Location:** `project-planning-system/`

**Responsibilities:**
- AI project analysis (Claude Haiku 4.5)
- Google Doc generation
- Database operations
- Stateless HTTP API

**Dependencies:**
- `anthropic` - AI processing
- `fastapi` - Web framework
- `google-api-python-client` - Docs creation
- `supabase` - Database client

**Endpoints:**
- `POST /brainstorm` - Generate project plan
- `GET /projects/{discord_user_id}` - List user's projects
- `GET /projects/detail/{brainstorm_id}` - Get project details
- `GET /health` - Health check

---

### 2. **Discord Bot**
**Location:** `discord-bot/`

**Responsibilities:**
- User interaction (Discord commands)
- HTTP client to Planning API
- Response formatting

**Dependencies:**
- `discord.py` - Discord integration
- `httpx` - HTTP client (async)
- NO `anthropic` dependency ✅

**Commands:**
- `/brainstorm <idea>` → Calls `POST /brainstorm`
- `/my-projects` → Calls `GET /projects/{user_id}`

---

## 🔧 Configuration

### Discord Bot `.env`
```bash
# Project Planning API
PROJECT_PLANNING_API_URL=http://localhost:8001

# Google Drive (optional)
GOOGLE_DRIVE_PROJECT_PLANNING_FOLDER_ID=your_folder_id

# Discord, Supabase, etc. (existing config)
...
```

### Planning API `.env`
```bash
# AI Service
ANTHROPIC_API_KEY=your_key_here

# Google Docs
GOOGLE_CREDENTIALS_PATH=/path/to/service-account.json
GOOGLE_DRIVE_PROJECT_PLANNING_FOLDER_ID=your_folder_id
GOOGLE_DELEGATED_USER_EMAIL=your-email@domain.com

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key

# Server
PORT=8001
```

---

## 🚀 Running the System

### 1. Start Planning API

```bash
cd project-planning-system

# Create venv and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your keys

# Start server
./run.sh
```

Server starts on `http://localhost:8001`

Verify: `curl http://localhost:8001/health`

---

### 2. Start Discord Bot

```bash
cd discord-bot

# Make sure Planning API URL is set
echo "PROJECT_PLANNING_API_URL=http://localhost:8001" >> .env

# Start bot
source .venv/bin/activate
./run.sh
```

Bot connects to Discord and Planning API.

---

## 🧪 Testing

### Test Planning API Directly

```bash
# Health check
curl http://localhost:8001/health

# Brainstorm (takes ~30-60 seconds)
curl -X POST http://localhost:8001/brainstorm \
  -H "Content-Type: application/json" \
  -d '{
    "project_idea": "Build a task dashboard",
    "discord_user_id": 123456789,
    "discord_username": "testuser"
  }'

# List projects
curl http://localhost:8001/projects/123456789
```

### Test via Discord

```
/brainstorm Build a monitoring system for GitHub activity
```

Expected:
1. Bot responds "Analyzing..."
2. ~30-60 seconds processing
3. Bot returns project summary + Google Doc link

---

## 📊 Data Flow

### Brainstorm Command Flow

1. **User in Discord:** `/brainstorm Build a dashboard`

2. **Discord Bot:**
   ```python
   POST http://localhost:8001/brainstorm
   {
     "project_idea": "Build a dashboard",
     "discord_user_id": 12345,
     "discord_username": "user#1234"
   }
   ```

3. **Planning API:**
   - Calls Claude Haiku AI (30-40 seconds)
   - Generates milestones and tasks
   - Creates Google Doc (5-10 seconds)
   - Saves to database

4. **Planning API Response:**
   ```json
   {
     "brainstorm_id": "uuid",
     "title": "Task Completion Dashboard",
     "doc_url": "https://docs.google.com/...",
     "summary": {
       "total_milestones": 6,
       "total_tasks": 28,
       "total_estimated_hours": 184
     }
   }
   ```

5. **Discord Bot:**
   - Formats response as embed
   - Shows project stats
   - Provides Google Doc link

---

## 🎯 Benefits of Separation

### ✅ Scalability
- Can scale Planning API independently
- Multiple Discord bots can use same API
- Can add web frontend later

### ✅ Clean Dependencies
- Discord bot doesn't need `anthropic`
- Planning API doesn't need `discord.py`
- Each service has minimal dependencies

### ✅ Development
- Test Planning API without Discord
- Develop features independently
- Easier debugging (separate logs)

### ✅ Deployment
- Deploy Planning API once
- Multiple bots in different servers
- Can restart bot without affecting API

---

## 📁 File Structure

```
alfred/
├── project-planning-system/          # FastAPI Service
│   ├── api/
│   │   ├── app.py                    # ✅ FastAPI application
│   │   └── models.py                 # ✅ Request/response models
│   ├── ai/
│   │   ├── prompts.py                # AI prompts
│   │   └── project_brainstormer.py   # Claude integration
│   ├── services/
│   │   └── doc_generator.py          # Google Docs formatter
│   ├── .env.example                  # ✅ Config template
│   ├── requirements.txt              # ✅ Dependencies
│   └── run.sh                        # ✅ Startup script
│
├── discord-bot/                      # Discord Client
│   ├── bot/
│   │   ├── bot.py                    # Main bot (modified)
│   │   └── project_planning.py       # ✅ HTTP client commands
│   └── pyproject.toml                # ✅ No anthropic dependency
│
└── shared-services/
    └── database/migrations/
        └── 004_project_brainstorms.sql  # Database schema
```

---

## 🔒 Security Notes

1. **API Authentication:** Currently none (localhost only)
   - For production: Add API key or JWT
   - Use internal network or VPN

2. **Secrets Management:**
   - Planning API: Stores AI keys
   - Discord Bot: Only Discord token
   - Never expose Planning API publicly

3. **Rate Limiting:**
   - Add rate limiting in production
   - Claude API has rate limits
   - Protect against abuse

---

## 🚧 Future Enhancements

### Phase 5: ClickUp Publisher (Next)
- `POST /publish-project` endpoint
- Parse Google Doc → Create ClickUp tasks
- Store `clickup_list_id` in database

### Phase 6: Web Frontend
- React/Next.js app
- Same Planning API backend
- Browse all projects, create plans

### Phase 7: Webhooks
- ClickUp webhooks → Update status
- Real-time project tracking
- Notify Discord on task completion

---

## 📝 Summary

| Component | Port | Dependencies | Role |
|-----------|------|--------------|------|
| **Planning API** | 8001 | anthropic, fastapi | AI processing, docs |
| **Discord Bot** | N/A | discord.py, httpx | User interface |
| **Database** | N/A | Supabase | Data persistence |

**Result:** Clean, scalable, testable architecture! 🎉
