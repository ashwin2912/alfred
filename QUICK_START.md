# Quick Start Guide - Discord-First Onboarding

Get the new onboarding system running in 15 minutes.

## Prerequisites

- ✅ Discord bot token (from earlier setup)
- ✅ Supabase project
- ✅ Discord server with admin access

## Step 1: Run Database Migration (5 min)

```bash
# Navigate to migrations
cd shared-services/database/migrations

# Run via Supabase dashboard:
# 1. Go to https://supabase.com/dashboard
# 2. Select your project
# 3. Go to SQL Editor
# 4. Copy entire contents of 002_add_teams_and_hierarchy.sql
# 5. Click "Run"
```

**Verify it worked:**
```sql
-- Should return 5 roles
SELECT * FROM roles ORDER BY level;

-- Should return 5 teams
SELECT * FROM teams;

-- Should show new columns
SELECT discord_id, role, team, status FROM team_members LIMIT 1;
```

## Step 2: Get Admin Channel ID (2 min)

1. In Discord, create channel: `#admin-onboarding`
2. Make it private (only admins)
3. Enable Developer Mode: Settings → Advanced → Developer Mode
4. Right-click channel → Copy ID
5. Save it (looks like: `1234567890123456789`)

## Step 3: Update Environment Variables (2 min)

Edit `discord-bot/.env`:

```bash
# Add this line
DISCORD_ADMIN_CHANNEL_ID=1234567890123456789

# Make sure these exist
DISCORD_BOT_TOKEN=your_token_from_before
DISCORD_GUILD_ID=your_server_id
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_service_role_key
SUPABASE_SERVICE_KEY=your_service_role_key  # Same as above
```

## Step 4: Install/Update Dependencies (3 min)

```bash
cd discord-bot

# Install bot
uv pip install -e .

# Install updated data-service (has new onboarding methods)
uv pip install -e ../shared-services/data-service --force-reinstall
```

## Step 5: Run the Bot (1 min)

```bash
./run.sh
```

**You should see:**
```
2025-12-10 - INFO - Starting bot...
2025-12-10 - INFO - Synced commands globally (DMs enabled)
2025-12-10 - INFO - Synced commands to guild 123456789
2025-12-10 - INFO - TeamBot#1234 has connected to Discord!
```

## Step 6: Test It! (2 min)

### Test with a Second Account

1. **Join Server**: Use a second Discord account or ask a friend
2. **Check DM**: Should receive welcome message with button
3. **Click Button**: Opens onboarding form
4. **Fill Form**: 
   - Name: Test User
   - Email: test@example.com
   - Role: Engineer
   - Team: Engineering
5. **Submit**: 
6. **Check Admin Channel**: Should see approval request
7. **Click ✅ Approve**: 
8. **Check Original User**: Should get approval DM

### Test Existing Commands

```
/setup           → Check profile status
/help            → Show all commands
/my-tasks        → View ClickUp tasks (after setup)
```

## What Changed?

### New Features ✨
- Auto-welcome DMs when users join
- Interactive onboarding forms (Discord modals)
- Admin approval workflow
- Team and role management
- Enhanced database schema

### Existing Features Still Work ✅
- `/setup` - Now shows more info (team, role, manager)
- `/setup-clickup` - Same as before
- `/my-tasks` - Same as before
- `/help` - Updated with new info

## Common Issues

### "No module named 'data_service'"
```bash
cd discord-bot
uv pip install -e ../shared-services/data-service --force-reinstall
```

### "Admin channel not found"
- Verify `DISCORD_ADMIN_CHANNEL_ID` in `.env`
- Make sure bot can access the channel
- Bot needs "View Channel" permission

### "Database error: relation does not exist"
- Migration didn't run
- Run migration in Supabase SQL Editor

### Bot doesn't respond to new members
- Check bot has "Server Members Intent" enabled in Discord Developer Portal
- Verify bot has "Send Messages" permission
- Check bot logs for errors

## Next Steps

### Immediate
1. ✅ Test onboarding flow end-to-end
2. ✅ Customize welcome message (edit `bot/bot.py`)
3. ✅ Add your team members to `teams` table

### This Week
1. Create admin commands (`/admin-pending`, `/admin-approve`)
2. Add role auto-assignment based on team
3. Integrate with Google Docs for profile creation

### This Month
1. Build analytics dashboard
2. Add skill-based task matching
3. Implement team hierarchy visualization

## Rollback Plan

If something breaks:

```bash
# Stop the bot
Ctrl+C

# Revert data-service
cd shared-services/data-service
git checkout HEAD~1

# Reinstall old version
cd ../../discord-bot
uv pip install -e ../shared-services/data-service --force-reinstall

# Restart
./run.sh
```

Database migration is additive (only adds tables/columns), so existing functionality won't break.

## Getting Help

- **Logs**: `tail -f discord-bot.log`
- **Database**: Check Supabase dashboard → Table Editor
- **Discord**: Verify bot online (green status)

## Success Checklist

- [ ] Migration ran successfully
- [ ] Bot starts without errors
- [ ] Admin channel receives notifications
- [ ] New members get welcome DM
- [ ] Onboarding form submits successfully
- [ ] Approval buttons work
- [ ] Existing commands still work

---

**Time to complete**: ~15 minutes
**Difficulty**: Moderate
**Required**: Database access, Discord admin

Ready? Let's go! 🚀
