# Alfred

Discord-based team management system with AI-powered project planning and automated onboarding.

---

## What It Does

- **Team Onboarding**: Automated Discord member onboarding with admin approval
- **Task Management**: View and manage ClickUp tasks directly from Discord
- **Project Planning**: AI-powered project breakdown and Google Docs generation
- **Team Management**: Create teams, assign members, track project lists

---

## Quick Start

### Prerequisites
- Discord bot token
- Supabase project (PostgreSQL + Auth)
- Google Cloud service account with Docs/Drive/Sheets API access
- Anthropic API key (for AI features)
- ClickUp workspace (optional, for task management)

### Local Setup

1. **Clone and install dependencies**
   ```bash
   git clone https://github.com/your-username/alfred.git
   cd alfred
   
   # Install uv package manager
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Sync dependencies for each service
   cd ai-core-service && uv sync && cd ..
   cd task-service && uv sync && cd ..
   cd discord-bot && uv sync && cd ..
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   Fill in:
   ```bash
   # Database
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your_service_key
   
   # AI
   ANTHROPIC_API_KEY=sk-ant-your-key
   
   # Google (optional)
   GOOGLE_CREDENTIALS_PATH=/path/to/service-account.json
   GOOGLE_DRIVE_FOLDER_ID=your_folder_id
   
   # Discord
   DISCORD_BOT_TOKEN=your_bot_token
   
   # ClickUp (optional)
   # Users configure their own tokens via /setup-clickup
   ```

3. **Run locally**
   ```bash
   # Start all services
   ./run-local.sh
   
   # Or run individually
   cd ai-core-service && uv run uvicorn api.app:app --port 8001
   cd task-service && uv run uvicorn api.app:app --port 8002
   cd discord-bot && uv run python -m bot.bot
   ```

4. **Test in Discord**
   ```
   /setup - Check onboarding status
   /my-tasks - View your ClickUp tasks
   /create-project - Generate AI project plan (Team Leads only)
   ```

---

## Production Deployment (GCP)

### One-Time Setup

1. **Create GCP VM**
   ```bash
   gcloud compute instances create alfred-prod \
     --zone=us-central1-a \
     --machine-type=e2-standard-2 \
     --image-family=ubuntu-2204-lts \
     --image-project=ubuntu-os-cloud \
     --tags=alfred-prod
   ```

2. **Configure firewall**
   ```bash
   gcloud compute firewall-rules create alfred-services \
     --direction=INGRESS \
     --action=allow \
     --rules=tcp:8001,tcp:8002 \
     --target-tags=alfred-prod
   ```

3. **SSH and setup**
   ```bash
   gcloud compute ssh alfred-prod --zone=us-central1-a
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # Clone repo
   git clone https://github.com/your-username/alfred.git /opt/alfred
   cd /opt/alfred
   
   # Configure .env
   cp .env.example .env
   nano .env
   
   # Upload Google credentials (from local machine)
   exit
   gcloud compute scp /path/to/service-account.json alfred-prod:/opt/alfred/credentials/service-account.json --zone=us-central1-a
   ```

4. **Deploy with Docker**
   ```bash
   gcloud compute ssh alfred-prod --zone=us-central1-a
   cd /opt/alfred
   docker compose up -d
   ```

### GitHub Actions CI/CD

See [`docs/CI_CD_SETUP.md`](docs/CI_CD_SETUP.md) for automated deployments on push to `main`.

**TL;DR:**
1. Create GCP service account with compute permissions
2. Add `GCP_SA_KEY` and `GCP_PROJECT_ID` to GitHub Secrets
3. Push to `main` → auto-deploys

---

## Architecture

```
alfred/
├── ai-core-service/          # AI project planning (Claude)
│   ├── ai/                   # Brainstorming logic
│   ├── api/                  # FastAPI endpoints
│   └── services/             # Doc generation
├── task-service/             # ClickUp integration
│   ├── api/                  # Task endpoints
│   └── services/             # ClickUp client
├── discord-bot/              # Discord interface
│   └── bot/                  # Commands and onboarding
├── shared-services/
│   ├── data-service/         # Supabase client
│   └── docs-service/         # Google APIs
└── deployment/               # Deploy scripts
```

**Data Flow:**
```
Discord → Bot → Task Service → ClickUp API
                  ↓
            Data Service → Supabase
                  ↓
         AI Core Service → Claude → Google Docs
```

---

## Key Commands

### Team Leads
- `/create-project <idea>` - Generate AI project plan
- `/publish-project <doc_url>` - Publish plan to ClickUp
- `/team-report` - View team's task status

### Team Members
- `/setup` - Check onboarding status
- `/setup-clickup <token>` - Connect ClickUp account
- `/my-tasks` - View your tasks (filtered by team/channel)

### Admins
- `/create-team` - Create new team
- `/add-project-list` - Add ClickUp list to team
- `/list-project-lists` - View team's lists

---

## Tech Stack

- **Framework**: FastAPI (services), discord.py (bot)
- **Database**: Supabase (PostgreSQL + Auth)
- **AI**: Anthropic Claude 4.5
- **Documents**: Google Docs/Drive/Sheets APIs
- **Tasks**: ClickUp API
- **Deployment**: Docker Compose, GitHub Actions
- **Language**: Python 3.11+
- **Package Manager**: uv

---

## Documentation

### Setup & Deployment
- [`docs/DATABASE_SETUP.md`](docs/DATABASE_SETUP.md) - Database schema and setup
- [`docs/MANUAL_DEPLOYMENT.md`](docs/MANUAL_DEPLOYMENT.md) - Step-by-step GCP setup
- [`docs/CI_CD_SETUP.md`](docs/CI_CD_SETUP.md) - GitHub Actions automation

### Operations
- [`docs/MONITORING.md`](docs/MONITORING.md) - Health checks and troubleshooting

### Features
- [`docs/SIMPLIFIED_ONBOARDING_FLOW.md`](docs/SIMPLIFIED_ONBOARDING_FLOW.md) - Onboarding process
- [`docs/ACTION_REQUEST_SYSTEM_PLAN.md`](docs/ACTION_REQUEST_SYSTEM_PLAN.md) - Action system design

---

## Contributing

1. Create feature branch
2. Make changes
3. Test locally with `./run-local.sh`
4. Push - CI/CD auto-deploys to production

---

## License

MIT

---

**Status**: Production  
**Version**: 2.0.0  
**Last Updated**: Dec 27, 2024
