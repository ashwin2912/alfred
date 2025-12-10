# Discord Team Bot

Discord bot for team management and ClickUp integration. Allows team members to connect their ClickUp accounts and manage tasks directly from Discord.

## Features

- **Profile Management**: Check onboarding status and view profile information
- **ClickUp Integration**: Connect ClickUp account and manage tasks
- **Task Viewing**: View assigned tasks from ClickUp lists
- **Secure**: All interactions are ephemeral (only visible to the user)

## Setup

### 1. Install Dependencies

```bash
cd discord-bot
uv pip install -e .
```

### 2. Install Shared Services

The bot depends on the data-service for team member management:

```bash
cd ../shared-services/data-service
uv pip install -e .
```

### 3. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section and click "Add Bot"
4. Under "Privileged Gateway Intents", enable:
   - Server Members Intent
   - Message Content Intent
5. Click "Reset Token" and copy your bot token
6. Go to OAuth2 → URL Generator:
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Send Messages`, `Use Slash Commands`, `Read Messages/View Channels`
7. Copy the generated URL and use it to invite the bot to your server

### 4. Configure Environment

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Required variables:
- `DISCORD_BOT_TOKEN`: Your bot token from Discord Developer Portal
- `DISCORD_GUILD_ID`: Your Discord server/guild ID (right-click server → Copy ID)
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase service role key

To get your Discord Guild ID:
1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click your server name and select "Copy ID"

### 5. Run the Bot

```bash
uv run python -m bot.bot
```

Or create a run script:

```bash
#!/bin/bash
cd discord-bot
uv run python -m bot.bot
```

## Commands

All commands are slash commands and are only visible to the user who runs them (ephemeral).

**💬 DM Support:** All commands work in both server channels and direct messages with the bot!

### `/setup`
Check your onboarding status and profile information. Shows:
- Profile details (email, bio, etc.)
- ClickUp integration status
- Link to profile document

**Usage:**
```
/setup
```

### `/setup-clickup <token>`
Connect your ClickUp account by providing your API token.

**How to get your ClickUp token:**
1. Go to [ClickUp Settings → Apps](https://app.clickup.com/settings/apps)
2. Click "Generate" under API Token
3. Copy the token

**Usage:**
```
/setup-clickup pk_123456789_ABCDEFGH
```

The bot will:
- Validate your token
- Save it securely in the database
- Show your ClickUp username

### `/my-tasks`
View all your assigned tasks across all ClickUp teams and lists.

**Usage:**
```
/my-tasks
```

Shows up to 10 tasks with:
- Task name
- Status
- Priority
- Due date
- Link to task in ClickUp

**Note:** Automatically fetches all tasks assigned to you from all teams you have access to. No need to specify list IDs!

### `/help`
Show all available commands and usage instructions.

**Usage:**
```
/help
```

## Architecture

```
discord-bot/
├── bot/
│   ├── __init__.py
│   ├── bot.py           # Main bot logic and commands
│   ├── config.py        # Configuration and environment variables
│   └── services.py      # Services for data access and ClickUp API
├── .env.example         # Example environment configuration
├── pyproject.toml       # Project dependencies
└── README.md           # This file
```

### Services

**TeamMemberService** (`bot/services.py`)
- Manages team member data via data-service
- Methods:
  - `get_member_by_discord(discord_username)`: Get member by Discord username
  - `update_clickup_token(discord_username, token)`: Save ClickUp token

**ClickUpService** (`bot/services.py`)
- Interacts with ClickUp API
- Methods:
  - `validate_token()`: Validate API token
  - `get_user_info()`: Get authenticated user info
  - `get_tasks(list_id, assigned_only)`: Fetch tasks from list

## User Flow

1. **Onboarding**: User completes onboarding through onboarding-app
   - Provides Discord username during onboarding
   - Profile saved to database with `discord_username` field

2. **Discord Setup**: User joins Discord server and runs `/setup`
   - Bot checks if profile exists by Discord username
   - Shows profile status and ClickUp integration status

3. **ClickUp Connection**: User runs `/setup-clickup <token>`
   - Bot validates token with ClickUp API
   - Saves token to database (encrypted at rest by Supabase)
   - Confirms connection with ClickUp username

4. **Task Management**: User runs `/my-tasks <list_id>`
   - Bot fetches tasks using saved ClickUp token
   - Displays tasks with status, priority, and due dates

## Security

- All slash commands are ephemeral (only visible to the user)
- ClickUp tokens are validated before saving
- Tokens are stored encrypted at rest in Supabase
- Bot uses service role key for database access
- No tokens or sensitive data are logged

## Troubleshooting

### Bot doesn't respond to commands
- Make sure the bot is online (check Discord)
- Verify the bot has proper permissions in your server
- Check that slash commands are synced (restart bot if needed)

### "Profile Not Found" error
- Verify you completed the onboarding process
- Check that your Discord username matches what you provided during onboarding
- Contact an admin to verify your profile in the database

### "Invalid Token" when setting up ClickUp
- Make sure you copied the entire token
- Generate a new token from ClickUp settings
- Verify your ClickUp account is active

### "No Tasks Found"
- Verify the list ID is correct
- Check that you have tasks assigned to you in that list
- Make sure your ClickUp token is still valid

## Development

### Running in Development

```bash
# Install dependencies
uv pip install -e .
uv pip install -e ../shared-services/data-service

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env

# Run the bot
uv run python -m bot.bot
```

### Testing Commands

After starting the bot:
1. Go to your Discord server
2. Type `/` to see available commands
3. Test each command:
   - `/setup` - Check profile status
   - `/setup-clickup <token>` - Connect ClickUp
   - `/my-tasks <list_id>` - View tasks
   - `/help` - View help

## Deployment

For production deployment:

1. Use a process manager like systemd or supervisord
2. Set up proper logging
3. Use environment variables instead of .env file
4. Monitor bot uptime and errors
5. Set up alerts for bot disconnections

Example systemd service:

```ini
[Unit]
Description=Discord Team Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/alfred/discord-bot
Environment="DISCORD_BOT_TOKEN=your_token"
Environment="SUPABASE_URL=your_url"
Environment="SUPABASE_KEY=your_key"
Environment="DISCORD_GUILD_ID=your_guild_id"
ExecStart=/path/to/uv run python -m bot.bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Future Enhancements

Possible features to add:
- Task creation and updates from Discord
- Task status changes
- Task assignment
- Due date reminders
- Team member lookup
- Skill-based task matching
- Integration with other tools (GitHub, Slack, etc.)
