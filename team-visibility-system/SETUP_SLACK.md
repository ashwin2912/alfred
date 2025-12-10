# Slack Setup Guide

This guide will help you set up Slack integration for automated team visibility reports.

## Option 1: Webhook URL (Recommended for Quick Setup)

This is the simplest method - just sends messages to a specific channel.

### Steps:

1. **Create an Incoming Webhook in Slack:**
   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name it "Alfred Team Visibility" and select your workspace
   - Click "Incoming Webhooks" in the sidebar
   - Toggle "Activate Incoming Webhooks" to ON
   - Click "Add New Webhook to Workspace"
   - Select the channel where reports should be posted (e.g., `#team-updates`)
   - Click "Allow"

2. **Copy the Webhook URL:**
   - You'll see a webhook URL like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`
   - Copy this URL

3. **Add to your `.env` file:**
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

4. **Test the integration:**
   ```bash
   python send_reports.py test
   ```

### Pros:
- ✅ Very simple setup (< 5 minutes)
- ✅ No additional permissions needed
- ✅ Works great for posting reports to a single channel

### Cons:
- ❌ Can only post to one specific channel
- ❌ Cannot upload files or use advanced features

---

## Option 2: Bot Token (Advanced)

Use this method if you need to:
- Post to multiple channels
- Upload files to Slack
- Use advanced Slack API features

### Steps:

1. **Create a Slack App:**
   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name it "Alfred Team Visibility" and select your workspace

2. **Configure Bot Permissions:**
   - Click "OAuth & Permissions" in the sidebar
   - Scroll to "Scopes" → "Bot Token Scopes"
   - Add these scopes:
     - `chat:write` - Send messages
     - `chat:write.public` - Send to public channels without joining
     - `files:write` - Upload files (optional)

3. **Install App to Workspace:**
   - Scroll to top of "OAuth & Permissions" page
   - Click "Install to Workspace"
   - Click "Allow"

4. **Copy the Bot Token:**
   - You'll see "Bot User OAuth Token" starting with `xoxb-`
   - Copy this token

5. **Add to your `.env` file:**
   ```bash
   SLACK_BOT_TOKEN=xoxb-your-token-here
   SLACK_CHANNEL=#team-updates
   ```

6. **Test the integration:**
   ```bash
   python send_reports.py test
   ```

### Pros:
- ✅ Can post to any channel (just change `SLACK_CHANNEL` env var)
- ✅ Can upload files
- ✅ More flexible for future features

### Cons:
- ❌ Slightly more complex setup
- ❌ Requires managing OAuth tokens

---

## Testing Your Setup

After configuring either option, test it:

```bash
# Send a test message
python send_reports.py test

# Send a daily report
python send_reports.py daily

# Send a weekly report
python send_reports.py weekly
```

---

## Troubleshooting

### Error: "Either SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN must be provided"
- Make sure you added the webhook URL or bot token to your `.env` file
- Run `source .env` or restart your terminal

### Error: "Invalid webhook URL"
- Verify the webhook URL is correct (starts with `https://hooks.slack.com/services/`)
- Make sure there are no extra spaces or quotes

### Error: "Channel not found"
- If using bot token, make sure the bot has access to the channel
- Channel names should start with `#` (e.g., `#team-updates`)
- Or use channel ID (e.g., `C1234567890`)

### Messages not appearing in Slack
- Check the webhook URL is for the correct workspace
- Verify the bot is installed in your workspace
- Make sure the channel exists and you have access to it

---

## Scheduling Automated Reports

### Using cron (Linux/Mac)

Edit your crontab:
```bash
crontab -e
```

Add these lines:

```bash
# Daily report at 9 AM (Monday-Friday)
0 9 * * 1-5 cd /path/to/team-visibility-system && python send_reports.py daily

# Weekly report on Friday at 4 PM
0 16 * * 5 cd /path/to/team-visibility-system && python send_reports.py weekly
```

### Using GitHub Actions (Cloud-based)

Create `.github/workflows/daily-report.yml`:

```yaml
name: Daily Team Report

on:
  schedule:
    - cron: '0 9 * * 1-5'  # 9 AM weekdays
  workflow_dispatch:  # Allow manual trigger

jobs:
  send-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python send_reports.py daily
        env:
          CLICKUP_API_TOKEN: ${{ secrets.CLICKUP_API_TOKEN }}
          CLICKUP_LIST_ID: ${{ secrets.CLICKUP_LIST_ID }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

Then add your secrets in GitHub repository settings.

---

## Best Practices

1. **Start with a test channel**: Test reports in a private channel before sending to the whole team
2. **Set up both daily and weekly**: Daily for quick updates, weekly for comprehensive reviews
3. **Adjust timing**: Schedule reports when your team is most active
4. **Monitor API costs**: Claude API calls cost money - consider limiting individual summaries for large teams
5. **Keep webhook URLs secret**: Don't commit them to git - always use `.env` file

---

## Example Report Output

### Daily Report
- Executive summary of team progress
- Today's activity (tasks updated in last 24 hours)
- Critical blockers
- Team overview (AI-generated)
- Individual standup summaries

### Weekly Report
- Tasks completed this week
- Team performance overview
- Blocker analysis
- Key decisions made
- Individual contributions
- High-priority tasks for next week

---

## Need Help?

- Slack API Documentation: https://api.slack.com/
- Webhook Guide: https://api.slack.com/messaging/webhooks
- Block Kit Builder: https://app.slack.com/block-kit-builder (for customizing message format)
