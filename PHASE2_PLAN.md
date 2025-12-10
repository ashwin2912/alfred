# Phase 2: Discord Bot Implementation

## Goal
Build Discord bot that allows users to:
1. Set up their ClickUp integration via Discord
2. View and manage their ClickUp tasks
3. Update task status from Discord

---

## User Flow

### Initial Setup
```
1. Admin creates Supabase user
2. User completes onboarding form (includes Discord username)
3. User joins Discord server
4. User runs /setup command
   → Bot checks if Discord username exists in team_members
   → If yes: "Found your profile! Now set up ClickUp with /setup-clickup"
   → If no: "Please complete onboarding first at: [link]"
5. User runs /setup-clickup <token>
   → Bot validates token with ClickUp API
   → Bot fetches ClickUp user ID
   → Bot saves token + user ID to team_members table
   → Success! User can now use /my-tasks
```

### Daily Usage
```
User: /my-tasks
→ Bot looks up user by Discord username
→ Gets clickup_api_token from database
→ Fetches tasks from ClickUp API
→ Displays formatted task list

User: /complete 123
→ Bot updates task status in ClickUp
→ Confirms to user
```

---

## Architecture

```
Discord User
    ↓
Discord Bot (discord.py)
    ↓
GET /team/members/discord/{username}  ← Lookup user
    ↓
team_members table
    ↓ (returns clickup_api_token)
Discord Bot
    ↓
ClickUp API (using user's token)
    ↓
Returns tasks
    ↓
Discord Bot formats & displays
```

---

## Tech Stack

- **discord.py** - Discord bot framework
- **requests** - HTTP client for ClickUp API
- **Existing API** - Use `/team/members/discord/{username}` endpoint
- **Environment**: Can run as separate service or integrate into onboarding-app

---

## Bot Commands to Implement

### Phase 2A: Setup (Priority 1)
| Command | Description | Implementation |
|---------|-------------|----------------|
| `/setup` | Check profile exists | Query team_members by discord_username |
| `/setup-clickup <token>` | Save ClickUp token | POST /team/me/clickup-token |

### Phase 2B: Task Management (Priority 2)
| Command | Description | ClickUp API |
|---------|-------------|-------------|
| `/my-tasks` | List user's tasks | GET /api/v2/team/{team_id}/task (filter by assignee) |
| `/task <id>` | Task details | GET /api/v2/task/{task_id} |
| `/update <id> <status>` | Update status | PUT /api/v2/task/{task_id} |
| `/complete <id>` | Mark complete | PUT /api/v2/task/{task_id} (status=complete) |

### Phase 2C: Team Features (Priority 3)
| Command | Description | API |
|---------|-------------|-----|
| `/team` | List team | GET /team/members |
| `/skills <skill>` | Find by skill | GET /team/members/skill/{skill} |
| `/assign <task> @user` | Assign task | PUT /api/v2/task/{task_id} |

---

## Implementation Steps

### Step 1: Discord Bot Setup (30 min)
1. Create bot in Discord Developer Portal
2. Get bot token
3. Invite bot to server
4. Test connection

### Step 2: Basic Bot Structure (1 hour)
```python
# discord_bot/bot.py
import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} is ready!')

@bot.slash_command(name="setup")
async def setup(ctx):
    # Check if user exists in team_members
    pass

@bot.slash_command(name="setup-clickup")
async def setup_clickup(ctx, token: str):
    # Save token to database
    pass

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
```

### Step 3: Integrate with Team API (2 hours)
- Implement user lookup by Discord username
- Implement token saving
- Error handling and user feedback

### Step 4: ClickUp Integration (2 hours)
- Fetch tasks from ClickUp
- Format and display in Discord
- Update task status

### Step 5: Testing (1 hour)
- Test full flow: onboard → Discord setup → view tasks
- Handle edge cases (user not found, invalid token, etc.)

---

## File Structure

```
alfred/
├── discord-bot/              # NEW
│   ├── bot.py                # Main bot
│   ├── commands/
│   │   ├── setup.py          # Setup commands
│   │   ├── tasks.py          # Task management
│   │   └── team.py           # Team commands
│   ├── services/
│   │   ├── api_client.py     # Alfred API client
│   │   └── clickup_client.py # ClickUp API client
│   ├── .env
│   ├── pyproject.toml
│   └── README.md
│
├── onboarding-app/           # EXISTING
└── shared-services/          # EXISTING
```

---

## Environment Variables

### discord-bot/.env
```bash
# Discord
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_server_id

# Alfred API
ALFRED_API_URL=http://localhost:8000

# ClickUp (for admin operations if needed)
CLICKUP_API_TOKEN=your_admin_token
CLICKUP_WORKSPACE_ID=your_workspace_id
```

---

## Discord Bot Permissions

Required permissions:
- Send Messages
- Send Messages in Threads
- Embed Links
- Read Message History
- Use Slash Commands

OAuth2 URL Generator:
- Scope: `bot`, `applications.commands`
- Permissions: Select above

---

## Security Considerations

### ClickUp Token Storage
✅ **Good**: Store in database encrypted (future)
✅ **Current**: Store in database with RLS policies
❌ **Bad**: Store in Discord messages or bot memory

### Token Validation
- Validate token by calling ClickUp API before saving
- Don't store invalid tokens
- Provide clear error messages

### User Privacy
- Only show user's own tasks (don't leak other users' tasks)
- DM sensitive commands (token setup should be in DMs)
- Rate limiting to prevent abuse

---

## Error Handling

### User Not Found
```
User: /setup
Bot: "❌ I couldn't find your profile. 
      Make sure you completed onboarding with Discord username: username#1234
      Onboarding link: [link]"
```

### Invalid Token
```
User: /setup-clickup invalid_token
Bot: "❌ Invalid ClickUp API token. 
      Get your token at: https://app.clickup.com/settings/apps
      Then try again: /setup-clickup <your_token>"
```

### No Tasks
```
User: /my-tasks
Bot: "📋 You have no tasks assigned in ClickUp.
      Ask your team lead to assign some tasks!"
```

---

## Testing Checklist

### Setup Flow
- [ ] User not in database → Error message
- [ ] User in database, no Discord username → Error message
- [ ] User in database with Discord username → Success
- [ ] Invalid ClickUp token → Error with instructions
- [ ] Valid ClickUp token → Success + confirmation

### Task Management
- [ ] User has tasks → Display list
- [ ] User has no tasks → Friendly message
- [ ] Update task status → Confirm success
- [ ] Invalid task ID → Error message

### Edge Cases
- [ ] Bot offline → Graceful degradation
- [ ] ClickUp API down → Error message
- [ ] Rate limit hit → Inform user to wait
- [ ] Malformed commands → Help text

---

## Phase 2 Success Criteria

✅ User can run `/setup` and get confirmation
✅ User can provide ClickUp token via `/setup-clickup`
✅ Token is validated and saved to database
✅ User can run `/my-tasks` and see their ClickUp tasks
✅ User can update task status from Discord
✅ All errors handled gracefully with helpful messages

---

## Estimated Timeline

- **Setup & Basic Bot**: 2 hours
- **API Integration**: 2 hours  
- **ClickUp Integration**: 3 hours
- **Testing & Polish**: 2 hours
- **Total**: ~9 hours (1-2 days)

---

## Next Actions

1. Create Discord bot in Developer Portal
2. Set up basic bot structure
3. Implement `/setup` command
4. Implement `/setup-clickup` command
5. Implement `/my-tasks` command
6. Test end-to-end flow

---

**Ready to start?** Let me know and I'll help you create the Discord bot!
