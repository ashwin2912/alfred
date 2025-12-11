# Alfred Discord Bot - Quick Start

## 🎯 Fresh Setup (Recommended)

If you want to start completely fresh with your own teams:

### 1. Clean Up Existing Setup

```bash
cd discord-bot
source .venv/bin/activate
python scripts/cleanup_everything.py
```

This will:
- Delete Discord roles
- Clear database references
- Show you which Google Drive folders to delete manually

### 2. Run Interactive Setup

```bash
python scripts/interactive_setup.py
```

You'll be asked:
- **Which teams to create** (defaults, select from defaults, or custom)
- **Your Discord ID, name, email** (for admin account)

The script creates:
- ✅ Teams in database
- ✅ Discord roles with colors
- ✅ Google Drive folders + rosters
- ✅ Admin account

### 3. Start the Bot

```bash
./run.sh
```

### 4. Test

Run `/start-onboarding` and approve in `#admin-onboarding`

---

## 🚀 First Time Setup (Manual - 5 Steps)

### 1. Fix Bot Permissions in Discord
⚠️ **IMPORTANT** - Do this first!

1. Go to your Discord Server
2. Server Settings → Roles
3. Find your bot's role (usually named "alfred" or similar)
4. Enable: **✅ Manage Roles**
5. **Drag the bot's role ABOVE the team roles** (Engineering, Product, Business)

### 2. Set Up Domain-Wide Delegation

1. Go to: https://admin.google.com/ac/owl/domainwidedelegation
2. Click "Add new"
3. Enter:
   - **Client ID**: `113119054929550733224`
   - **Scopes**: `https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets`
4. Click "Authorize"

### 3. Configure Environment

```bash
cd discord-bot
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
- `DISCORD_BOT_TOKEN`
- `DISCORD_GUILD_ID`
- `DISCORD_ADMIN_CHANNEL_ID`
- `DISCORD_ALFRED_CHANNEL_ID`
- `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- `GOOGLE_CREDENTIALS_PATH` (full path!)
- `GOOGLE_DRIVE_FOLDER_ID=1V9UK2U4xKzkALFKDzO1hu5Eg19Uu-qDG`
- `GOOGLE_DELEGATED_USER_EMAIL=partnerships@bulkmagic.us`

### 4. Run Complete Setup

```bash
cd discord-bot
source .venv/bin/activate
python scripts/setup_everything.py
```

Enter your:
- Discord ID (right-click profile → Copy ID)
- Full name
- Email

### 5. Start the Bot

```bash
./run.sh
```

---

## ✅ Quick Test

1. Run `/start-onboarding` in Discord
2. Fill out the form
3. Go to `#admin-onboarding` channel
4. Click "✅ Approve & Assign"
5. Select team (Engineering/Product/Business)
6. Enter role (optional)
7. Submit

**Expected Results**:
- ✅ User gets team role (colored name)
- ✅ Profile created in Google Drive
- ✅ Added to team roster
- ✅ User receives welcome DM

---

## 🔧 Common Issues

### Bot can't create roles
**Fix**: Give bot "Manage Roles" permission + move role higher in hierarchy

### Google Docs not created
**Fix**: Complete domain-wide delegation setup (Step 2 above)

### Team not found
**Fix**: Run database migrations in Supabase

---

## 📚 Full Documentation

See **SETUP_GUIDE.md** for complete step-by-step instructions.

---

## 🗑️ Reset for Testing

```bash
# Keep admin, delete test users
python scripts/reset_database.py
# Enter your Discord ID when prompted

# Start completely fresh
python scripts/reset_database.py
# Press Enter to delete everything
python scripts/setup_everything.py
```

---

That's it! 🎉
