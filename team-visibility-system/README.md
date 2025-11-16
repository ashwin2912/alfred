# Team Visibility System

AI-powered team reporting from ClickUp to Slack. Generates daily and weekly summaries with Claude AI.

## Features

- 📊 Daily & weekly reports with AI-generated insights
- 🚨 Automatic blocker detection and analysis
- 💬 Direct delivery to Slack
- 🎯 Pulls from ClickUp tasks, comments, and activity

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure `.env`

```bash
cp .env.example .env
```

Required:
- `CLICKUP_API_TOKEN` - Get from ClickUp settings
- `CLICKUP_LIST_ID` - From ClickUp list URL
- `ANTHROPIC_API_KEY` - Get from console.anthropic.com
- `SLACK_BOT_TOKEN` - From api.slack.com/apps
- `SLACK_CHANNEL` - Channel name (e.g., `alfred-test`)

### 3. Run Reports

```bash
python send_reports.py test    # Test Slack
python send_reports.py daily   # Daily report
python send_reports.py weekly  # Weekly report
```

## What Reports Include

**Daily Report:**
- Tasks updated in last 24 hours
- Critical blockers with AI analysis
- Team overview
- Individual standup summaries

**Weekly Report:**
- Completed tasks
- Team performance overview
- Key decisions from comments
- Individual contributions
- Priorities for next week

## Automation

Schedule with cron:

```bash
# Daily at 9 AM weekdays
0 9 * * 1-5 cd /path/to/team-visibility-system && python send_reports.py daily

# Weekly on Friday at 4 PM
0 16 * * 5 cd /path/to/team-visibility-system && python send_reports.py weekly
```
