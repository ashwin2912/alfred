# Alfred Discord Bot - Complete Setup Guide

This guide will help you set up the Alfred Discord bot from scratch.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Database Setup](#database-setup)
4. [Discord Bot Setup](#discord-bot-setup)
5. [Google Cloud Setup](#google-cloud-setup)
6. [Run Setup Script](#run-setup-script)
7. [Testing the Bot](#testing-the-bot)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts
- **Discord Developer Account** - https://discord.com/developers
- **Supabase Account** - https://supabase.com
- **Google Cloud Account** - https://console.cloud.google.com
- **Google Workspace Admin Access** - For domain-wide delegation

### Required Software
- Python 3.11+
- Git
- `uv` package manager (or pip)

---

## Initial Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd alfred/discord-bot
```

### 2. Create Virtual Environment

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate

# Or using standard Python
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
uv pip install -e .
# or
pip install -e .
```

---

## Database Setup

### 1. Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click "New project"
3. Choose organization and name: `alfred`
4. Set a strong database password
5. Select region closest to you
6. Click "Create new project"

### 2. Run Database Migrations

1. In Supabase dashboard, go to **SQL Editor**
2. Run migrations in order:

**Migration 001 - Initial Schema**:
```sql
-- Copy contents from: shared-services/database/migrations/001_initial_schema.sql
-- Paste into SQL Editor and run
```

**Migration 002 - Teams and Hierarchy**:
```sql
-- Copy contents from: shared-services/database/migrations/002_add_teams_and_hierarchy.sql
-- Paste into SQL Editor and run
```

**Migration 003 - Google Drive Integration**:
```sql
-- Copy contents from: shared-services/database/migrations/003_add_google_drive_to_teams.sql
-- Paste into SQL Editor and run
```

### 3. Get Supabase Credentials

1. In Supabase dashboard, go to **Settings** → **API**
2. Copy:
   - **Project URL** (save as `SUPABASE_URL`)
   - **anon/public key** (save as `SUPABASE_KEY`)
   - **service_role key** (save as `SUPABASE_SERVICE_KEY`)

---

## Discord Bot Setup

### 1. Create Discord Application

1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Name it "Alfred" and click "Create"
4. Go to **Bot** section
5. Click "Add Bot" → "Yes, do it!"
6. **IMPORTANT**: Enable these Privileged Gateway Intents:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent
7. Click "Reset Token" and copy it (save as `DISCORD_BOT_TOKEN`)

### 2. Invite Bot to Server

1. Go to **OAuth2** → **URL Generator**
2. Select scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Select bot permissions:
   - ✅ **Manage Roles** (CRITICAL!)
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Read Message History
   - ✅ Use Slash Commands
   - ✅ Mention Everyone
4. Copy generated URL and open in browser
5. Select your server and authorize

### 3. Create Discord Channels

In your Discord server, create these channels:

1. **#alfred** - For welcome messages and general bot interactions
2. **#admin-onboarding** - For admin approval notifications (make it admin-only)

### 4. Get Discord IDs

Enable Developer Mode in Discord:
- User Settings → Advanced → Developer Mode → ON

Get IDs (right-click → Copy ID):
- **Server ID** (right-click server name) → `DISCORD_GUILD_ID`
- **#alfred channel ID** → `DISCORD_ALFRED_CHANNEL_ID`
- **#admin-onboarding channel ID** → `DISCORD_ADMIN_CHANNEL_ID`
- **Your user ID** (right-click your profile) → Save for later

---

## Google Cloud Setup

### 1. Create Google Cloud Project

1. Go to https://console.cloud.google.com
2. Click "Select a project" → "New Project"
3. Name: `alfred` (or your choice)
4. Click "Create"

### 2. Enable APIs

Enable these APIs:
- **Google Docs API**: https://console.cloud.google.com/apis/library/docs.googleapis.com
- **Google Drive API**: https://console.cloud.google.com/apis/library/drive.googleapis.com
- **Google Sheets API**: https://console.cloud.google.com/apis/library/sheets.googleapis.com

Click "Enable" on each.

### 3. Create Service Account

1. Go to **IAM & Admin** → **Service Accounts**
2. Click "Create Service Account"
3. Name: `alfred-google-drive-tool`
4. Click "Create and Continue"
5. Skip role assignment → "Continue"
6. Click "Done"

### 4. Create Service Account Key

1. Click on the service account you just created
2. Go to **Keys** tab
3. Click "Add Key" → "Create new key"
4. Choose **JSON** format
5. Click "Create"
6. Save the downloaded JSON file to:
   ```
   shared-services/docs-service/creds/alfred-<project-id>-<random>.json
   ```

### 5. Set Up Domain-Wide Delegation

**CRITICAL STEP** - Required for Google Docs/Sheets creation:

1. In service account details, copy the **Client ID** (long number)
2. Go to Google Workspace Admin Console: https://admin.google.com/ac/owl/domainwidedelegation
3. Click "Add new"
4. Paste **Client ID**: `<your-client-id>`
5. Add **OAuth Scopes** (comma-separated):
   ```
   https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets
   ```
6. Click "Authorize"

### 6. Create Google Drive Folder

1. Go to Google Drive: https://drive.google.com
2. Create a new folder: "Alfred Team Management"
3. Right-click folder → "Share"
4. Add service account email: `alfred-google-drive-tool@<project-id>.iam.gserviceaccount.com`
5. Give **Editor** permission
6. Copy folder ID from URL: 
   ```
   https://drive.google.com/drive/folders/1V9UK2U4xKzkALFKDzO1hu5Eg19Uu-qDG
                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                          This is the folder ID
   ```

---

## Configure Environment Variables

### 1. Create `.env` File

```bash
cd discord-bot
cp .env.example .env
```

### 2. Edit `.env` File

```bash
# Discord Configuration
DISCORD_BOT_TOKEN=<your-bot-token>
DISCORD_GUILD_ID=<your-server-id>
DISCORD_ALFRED_CHANNEL_ID=<alfred-channel-id>
DISCORD_ADMIN_CHANNEL_ID=<admin-onboarding-channel-id>

# Supabase Configuration
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_KEY=<your-anon-key>
SUPABASE_SERVICE_KEY=<your-service-role-key>

# ClickUp (optional for now)
CLICKUP_API_BASE_URL=https://api.clickup.com/api/v2

# Google Docs Configuration
GOOGLE_CREDENTIALS_PATH=/full/path/to/shared-services/docs-service/creds/alfred-*.json
GOOGLE_DRIVE_FOLDER_ID=<your-folder-id>
GOOGLE_DELEGATED_USER_EMAIL=<your-workspace-email>
```

**Important**: 
- Use **full absolute paths** for `GOOGLE_CREDENTIALS_PATH`
- `GOOGLE_DELEGATED_USER_EMAIL` should be your Google Workspace admin email

---

## Run Setup Script

Now run the automated setup script:

```bash
cd discord-bot
source .venv/bin/activate
python scripts/setup_everything.py
```

**You'll be prompted for**:
- Your Discord ID (the one you copied earlier)
- Your full name
- Your email

**The script will**:
1. ✅ Create your admin account in database
2. ✅ Verify teams exist (Engineering, Product, Business, etc.)
3. ✅ Create Discord roles with colors
4. ✅ Create Google Drive folder structure
5. ✅ Create Team Management folder
6. ✅ Create team folders with Overview docs and roster sheets
7. ✅ Link everything together

**Expected output**:
```
🚀 Alfred Bot - Complete Setup
============================================================

🤖 Bot logged in as alfred#6771
📍 Found guild: YourServer

STEP 1: Create Admin Account
✅ Created admin account: Your Name

STEP 2: Create Teams in Database
✅ Found 6 teams in database

STEP 3: Create Discord Roles
  ✅ Created Discord role 'Engineering'
  ✅ Created Discord role 'Product'
  ✅ Created Discord role 'Business'

STEP 4: Initialize Google Drive Folders
✅ Team Management folder: 1yURRoPkVJx...
  ✅ Created folder: Engineering
  ✅ Created folder: Product
  ✅ Created folder: Business

SETUP COMPLETE! 🎉
```

---

## Testing the Bot

### 1. Start the Bot

```bash
./run.sh
# or manually:
python -m bot.bot
```

**You should see**:
```
Logged in as alfred#6771
Ready! Serving in guild: YourServer
```

### 2. Test Onboarding Flow

#### As a Test User:

1. In Discord, run: `/start-onboarding`
2. Fill in the modal:
   - **Name**: Test User
   - **Email**: test@example.com
   - **Phone**: +1234567890
   - **Bio**: "Full-stack developer with React and Node.js experience"
3. Click "Submit"
4. You should see: "✅ Onboarding request submitted!"

#### As Admin (in #admin-onboarding):

1. You'll see an approval request embed
2. Click **"✅ Approve & Assign"**
3. A select menu appears with teams:
   - ⚙️ Engineering
   - 📱 Product
   - 💼 Business
4. Select a team (e.g., **Engineering**)
5. Modal appears for role (optional)
6. Enter: "Senior Developer"
7. Click "Submit"

#### What Should Happen:

✅ **Database**:
- `pending_onboarding` record updated to "approved"
- New record created in `team_members`

✅ **Google Drive**:
- Profile document created in "Team Management" folder
- User added to "Engineering - Active Team Members" roster
- Roster includes link to profile

✅ **Discord**:
- User gets "Engineering" role (blue colored name!)
- User receives welcome DM with team/role info

✅ **Admin Receives Checklist**:
```
📋 Admin Action Items

1️⃣ Team Member Record
✅ Created in database

2️⃣ Create Supabase User
⚠️ Create in Supabase dashboard

3️⃣ Add to ClickUp
⚠️ ACTION REQUIRED

✅ Discord role 'Engineering' assigned
📄 ✅ Profile created & added to team roster
```

### 3. Verify in Google Drive

1. Go to your Google Drive folder
2. Check **Team Management** folder:
   - Should see: "Test User - Team Profile.gdoc"
3. Check **Engineering** folder:
   - Open "Engineering - Active Team Members" spreadsheet
   - Should see Test User with link to profile

### 4. Verify in Supabase

1. Go to Supabase dashboard → Table Editor
2. Check `pending_onboarding`:
   - Status should be "approved"
3. Check `team_members`:
   - New record for Test User
   - `profile_doc_id` and `profile_url` populated

---

## Troubleshooting

### Bot doesn't respond to commands

**Issue**: `/start-onboarding` doesn't work

**Solutions**:
1. Check bot is running: `./run.sh`
2. Verify bot has "applications.commands" scope
3. Try `/help` to test if bot is responding
4. Check bot has permissions in the channel

---

### Missing Permissions Error (403)

**Issue**: `403 Forbidden (error code: 50013): Missing Permissions`

**Solutions**:
1. Verify bot has **Manage Roles** permission
2. In Discord Server Settings → Roles:
   - Bot's role must be **above** the roles it's trying to assign
   - Drag bot role higher in the list
3. Re-run setup script after fixing permissions

---

### Google Docs Not Created

**Issue**: "⚠️ Google Docs not configured"

**Solutions**:
1. **Check domain-wide delegation**:
   - Go to: https://admin.google.com/ac/owl/domainwidedelegation
   - Verify your service account is listed
   - Verify scopes include: `documents`, `drive`, `spreadsheets`

2. **Test manually**:
   ```bash
   python scripts/test_google_docs_integration.py
   ```

3. **Check credentials path**:
   - Verify `GOOGLE_CREDENTIALS_PATH` in `.env`
   - Use **absolute path**, not relative
   - File should exist and be readable

4. **Check delegated email**:
   - `GOOGLE_DELEGATED_USER_EMAIL` should be your Google Workspace admin email
   - Must be on the same domain as the service account

---

### Team Not Found in Database

**Issue**: `⚠️ Team 'Business' not found in database`

**Solutions**:
1. **Run migration 002**:
   ```sql
   -- In Supabase SQL Editor, run:
   -- Copy from: shared-services/database/migrations/002_add_teams_and_hierarchy.sql
   ```

2. **Or manually add team**:
   ```sql
   INSERT INTO teams (name, description) VALUES
   ('Business', 'Business development and partnerships');
   ```

---

### Discord Role Not Assigned

**Issue**: User doesn't get team role

**Solutions**:
1. **Check roles exist**:
   - Server Settings → Roles
   - Verify "Engineering", "Product", "Business" roles exist
   - Names must match **exactly** (case-sensitive)

2. **Check role hierarchy**:
   - Bot's role must be above team roles
   - Drag bot role higher in Server Settings → Roles

3. **Re-create roles**:
   ```bash
   # Delete roles manually in Discord
   # Re-run setup script
   python scripts/setup_everything.py
   ```

---

### User Not Added to Roster

**Issue**: Google Sheet roster doesn't update

**Solutions**:
1. **Check team has roster**:
   ```bash
   # In Supabase, check teams table
   SELECT name, roster_sheet_id FROM teams WHERE name = 'Engineering';
   ```
   - If `roster_sheet_id` is NULL, run setup script again

2. **Re-initialize folders**:
   ```bash
   python scripts/initialize_team_folders.py
   ```

---

## Resetting for Fresh Testing

If you want to test again from scratch:

```bash
# Option 1: Keep admin, delete test users
python scripts/reset_database.py
# Enter your admin Discord ID when prompted

# Option 2: Complete fresh start
python scripts/reset_database.py
# Press Enter to delete everything
python scripts/setup_everything.py
```

**Note**: Google Drive folders are NOT deleted, only database references. You may want to manually clean up test documents.

---

## Project Structure

```
alfred/
├── discord-bot/
│   ├── bot/
│   │   ├── bot.py              # Main bot
│   │   ├── onboarding.py       # Onboarding flow
│   │   └── services.py         # Service wrappers
│   ├── scripts/
│   │   ├── setup_everything.py     # ⭐ Complete setup
│   │   ├── initialize_team_folders.py
│   │   ├── reset_database.py
│   │   ├── create_admin.py
│   │   └── test_google_docs_integration.py
│   ├── .env                    # Configuration
│   ├── .env.example            # Template
│   └── run.sh                  # Start script
│
├── shared-services/
│   ├── data-service/           # Database operations
│   ├── docs-service/           # Google Docs/Drive/Sheets
│   │   └── creds/              # Service account credentials
│   └── database/
│       └── migrations/         # SQL migrations
│
└── SETUP_GUIDE.md             # This file
```

---

## Next Steps

After successful setup and testing:

1. **Add more team members**: Test the approval flow with real users
2. **Customize team roles**: Add more teams/roles as needed
3. **Configure ClickUp**: Add ClickUp integration for task management
4. **Set up monitoring**: Add logging and error tracking
5. **Deploy to production**: Consider hosting on a VPS or cloud platform

---

## Getting Help

If you encounter issues not covered in troubleshooting:

1. Check bot logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure all migrations have been run
4. Check Google Cloud and Discord permissions

---

## Security Best Practices

1. **Never commit `.env` file** - It's in `.gitignore` for a reason
2. **Rotate tokens regularly** - Discord bot token, Supabase keys
3. **Use service account** - Don't use personal Google account
4. **Limit permissions** - Only give bot permissions it needs
5. **Backup database** - Regular exports from Supabase

---

**Setup Complete!** 🎉

Your Alfred Discord bot is now ready to onboard team members with automated Google Docs profiles, team rosters, and Discord role management!
