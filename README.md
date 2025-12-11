# Alfred

**Fully automated team onboarding and management system for Discord-first organizations.**

Zero-touch onboarding: from Discord approval to Supabase account, Google Drive profile, and team assignment — all in 10 seconds.

---

## 🎯 What Alfred Does

### **Automated Member Onboarding** (95% Automated)
1. **User** submits onboarding form in Discord (`/start-onboarding`)
2. **Admin** approves with team selection (dropdown menu)
3. **Alfred automatically**:
   - ✅ Creates Supabase auth account (with secure password)
   - ✅ Creates database record with real user_id
   - ✅ Generates Google Doc profile
   - ✅ Updates team roster in Google Sheets
   - ✅ Assigns Discord role (color-coded by team)
   - ✅ Sends welcome message to user
   - ✅ Sends credentials to admin (ephemeral)

**Time**: 5 minutes manual → **10 seconds automated** (30x faster)

### **Organized Team Structure**
- **Google Drive**: Team folders with Overview docs + Active Members rosters
- **Database**: Complete member profiles with skills, availability, roles
- **Discord**: Auto-assigned team roles (Engineering 🔵, Product 🟢, Business 🟡)

### **Future-Ready Architecture**
- Supabase users created but not exposed (ready for web apps)
- Reusable services (data, docs, auth) for easy expansion
- Modular design for new features

---

## 🚀 Components

### 1. **discord-bot** (Primary System)
**Fully automated Discord-first onboarding with admin approval**

**Features**:
- Modal-based onboarding forms
- Admin approval with team dropdown (Select Menu)
- **Auto-creates Supabase users** (16-char secure passwords)
- **Auto-creates Google Doc profiles** (Team Management folder)
- **Auto-updates team rosters** (Google Sheets with profile links)
- Discord role auto-assignment (color-coded teams)
- ClickUp task integration (`/my-tasks`)

**Tech Stack**: discord.py, Supabase, Google Docs/Drive/Sheets APIs

---

### 2. **team-management-system**
**AI-powered ClickUp project setup with smart task assignment**

**Features**:
- Automated project creation (32 tasks, 5 milestones)
- Smart skill matching (60% skills + 40% availability)
- ClickUp API integration

**Tech Stack**: Python, ClickUp API, Anthropic Claude AI

---

### 3. **shared-services**
**Reusable services for all Alfred components**

**Services**:
- `data-service` - Supabase database + Auth API
- `docs-service` - Google Docs/Drive/Sheets integration
- Type-safe models (Pydantic)

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Discord bot token
- Supabase project
- Google Cloud service account
- Google Workspace (for domain-wide delegation)

### Complete Setup (2 minutes)

```bash
# 1. Clone and navigate
cd discord-bot
source .venv/bin/activate
uv pip install -e .

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Run interactive setup (creates teams, roles, folders)
python scripts/interactive_setup.py
# Choose teams: 1,2,3 (Engineering, Product, Business)

# 4. Start the bot
./run.sh
```

**That's it!** Test with `/start-onboarding` in Discord.

---

## 📖 Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete step-by-step setup (new users)
- **[QUICK_START.md](QUICK_START.md)** - Quick reference guide
- **[progress.md](progress.md)** - Full feature list, roadmap, and updates
- **[discord-bot/scripts/README.md](discord-bot/scripts/README.md)** - Utility scripts

---

## 🎨 Features Highlights

### Interactive Setup
```bash
python scripts/interactive_setup.py
```
Choose teams, customize colors, auto-creates everything:
- ✅ Teams in database
- ✅ Discord roles (10+ color options)
- ✅ Google Drive folders + rosters
- ✅ Admin account

### Clean Reset for Testing
```bash
python scripts/cleanup_everything.py
```
Safe cleanup of roles, database, and Drive folders.

### Automated Workflows
**On Approval** (all automatic):
1. Supabase user creation
2. Database record (real user_id)
3. Google Doc profile
4. Team roster update
5. Discord role assignment
6. User notification

**Only manual**: Adding to ClickUp (requires workspace admin)

---

## 🏗️ Architecture

```
alfred/
├── discord-bot/              # Primary onboarding system
│   ├── bot/
│   │   ├── bot.py           # Main bot
│   │   ├── onboarding.py    # Approval flow + automation
│   │   └── services.py      # Service wrappers
│   └── scripts/
│       ├── interactive_setup.py      # ⭐ Interactive setup
│       ├── cleanup_everything.py     # Reset helper
│       └── initialize_team_folders.py
│
├── shared-services/
│   ├── data-service/        # Database + Supabase Auth
│   │   └── data_service/
│   │       └── client.py    # create_supabase_user()
│   ├── docs-service/        # Google Docs/Drive/Sheets
│   └── database/migrations/ # SQL migrations
│
└── team-management-system/  # ClickUp automation
```

---

## 📊 Automation Stats

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Onboarding Time | 5 min | 10 sec | **30x faster** |
| Setup Time | 45 min | 2 min | **22x faster** |
| Automation Rate | 20% | 95% | **+75%** |
| Manual Steps | 6 | 1 | **-83%** |

---

## 🎯 What's Next

See [progress.md](progress.md) for detailed roadmap.

### Immediate Options:
1. **Web Access Management** - `/create-web-access`, `/reset-password` commands
2. **Member Lifecycle** - `/list-members`, `/deactivate-member`, `/member-info`
3. **Onboarding Analytics** - Stats dashboard, approval metrics

### Coming Soon:
- ClickUp integration (auto-add to workspace)
- Skills matrix and mentorship matching
- Task management from Discord
- Team goals and OKRs

---

## 🔧 Tech Stack

- **Discord Bot**: discord.py
- **Database**: Supabase (PostgreSQL)
- **Auth**: Supabase Auth API
- **Docs**: Google Docs/Drive/Sheets APIs
- **Task Management**: ClickUp API
- **AI**: Anthropic Claude (for task assignment)
- **Language**: Python 3.11+
- **Type Safety**: Pydantic models

---

## 📝 Testing

```bash
# Quick test (5 minutes)
python scripts/cleanup_everything.py  # Clean slate
python scripts/interactive_setup.py   # Setup teams
./run.sh                              # Start bot

# In Discord:
/start-onboarding                     # Submit as user
# Approve in #admin-onboarding        # Approve as admin

# Verify:
# ✅ Supabase user created
# ✅ Google Doc in Team Management
# ✅ Added to team roster
# ✅ Discord role assigned
```

---

## 🤝 Contributing

This is a personal project for team management automation. See `progress.md` for feature requests and roadmap.

---

## 📄 License

Private project - All rights reserved

---

**Last Updated**: Dec 11, 2024  
**Status**: ✅ Fully automated onboarding system operational  
**Version**: 1.0.0
