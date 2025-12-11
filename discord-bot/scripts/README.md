# Discord Bot - Utility Scripts

Helpful scripts for setup and troubleshooting.

## Setup Scripts

### `setup_everything.py` ⭐ **RECOMMENDED**
**Purpose**: Complete one-command setup for the entire bot

**When to use**: 
- First-time setup
- After database reset
- Setting up a new Discord server

**Usage**:
```bash
python scripts/setup_everything.py
# Follow the interactive prompts
```

**What it does**:
1. ✅ Creates admin account in database
2. ✅ Verifies teams exist in database (Engineering, Product, Business, etc.)
3. ✅ **Creates Discord roles automatically** (with colors!)
4. ✅ Links Discord roles to database teams
5. ✅ Creates Team Management folder in Google Drive
6. ✅ Creates folder structure for each team (Overview doc + roster sheet)
7. ✅ Updates database with all folder/sheet IDs

**Interactive prompts**:
- Your Discord ID (right-click profile → Copy ID)
- Your full name
- Your email

**Note**: Requires bot to be running temporarily. Safe to run multiple times - skips existing items.

---

### `create_admin.py`
**Purpose**: Create the first admin profile in the database

**When to use**: First-time setup before running the bot

**Usage**:
```bash
python scripts/create_admin.py
# Enter your Discord ID, name, and email
```

**Required**: Admin profile must exist to approve onboarding requests

---

### `initialize_team_folders.py`
**Purpose**: Initialize Google Drive folder structure for teams

**When to use**: 
- First-time setup to create folders for existing teams
- After adding new teams to the database

**Usage**:
```bash
python scripts/initialize_team_folders.py
```

**What it does**:
- ✅ Creates "Team Management" folder for all member profiles
- ✅ Creates folder for each team (Engineering, Product, Business)
- ✅ Creates Team Overview document per team
- ✅ Creates Active Team Members spreadsheet per team
- ✅ Updates team records in database with folder/sheet IDs

**Note**: Safe to run multiple times - skips teams that already have folders

---

## Troubleshooting Scripts

### `test_google_docs_integration.py`
**Purpose**: Verify Google Docs service is configured correctly

**When to use**: 
- First-time setup
- Troubleshooting profile creation issues

**Usage**:
```bash
python scripts/test_google_docs_integration.py
```

**Tests**:
- ✅ DocsService initialization
- ✅ Profile creation from template
- ✅ Document saved to Drive folder

---

### `debug_admin_channel.py`
**Purpose**: Resend approval notification and test channel permissions

**When to use**:
- Bot can't send to #admin-onboarding
- Need to resend a notification for testing
- Verify bot permissions

**Usage**:
```bash
python scripts/debug_admin_channel.py
```

**Note**: This script creates its own bot instance. Use `/resend-approval` command instead when possible.

---

## Notes

- All scripts use the same `.env` configuration as the bot
- Scripts are safe to run multiple times
- Run from discord-bot root directory for proper imports
