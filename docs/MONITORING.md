# Monitoring Guide

## Overview
How to monitor Alfred's health and debug issues in production.

---

## Quick Health Check

### From VM
```bash
# SSH into VM
gcloud compute ssh alfred-prod --zone=us-central1-a

# Check all services
docker compose ps

# Health endpoints
curl http://localhost:8001/health  # AI Core Service
curl http://localhost:8002/health  # Task Service
```

### From Local Machine
```bash
# Get VM external IP
EXTERNAL_IP=$(gcloud compute instances describe alfred-prod \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

# Test endpoints
curl http://$EXTERNAL_IP:8001/health
curl http://$EXTERNAL_IP:8002/health
```

Expected response:
```json
{
  "status": "healthy",
  "anthropic_configured": true,
  "database_configured": true
}
```

---

## Container Status

### View Running Containers
```bash
docker compose ps
```

Expected output:
```
NAME                 STATUS              PORTS
alfred-ai-core       Up 2 hours          0.0.0.0:8001->8001/tcp
alfred-task-service  Up 2 hours          0.0.0.0:8002->8002/tcp
alfred-discord-bot   Up 2 hours
```

### Resource Usage
```bash
# Real-time stats
docker stats

# One-time snapshot
docker stats --no-stream
```

---

## Logs

### View All Logs
```bash
cd /opt/alfred
docker compose logs -f
```

### Service-Specific Logs
```bash
# Discord Bot
docker compose logs -f discord-bot

# AI Core Service
docker compose logs -f ai-core-service

# Task Service
docker compose logs -f task-service
```

### Last N Lines
```bash
# Last 100 lines
docker compose logs --tail=100 discord-bot

# With timestamps
docker compose logs -f --timestamps discord-bot
```

### Save Logs to File
```bash
docker compose logs > alfred-logs-$(date +%F).txt
```

---

## Common Issues

### Discord Bot Offline

**Check logs:**
```bash
docker compose logs discord-bot | grep -i error
```

**Common causes:**
- Invalid `DISCORD_BOT_TOKEN`
- Missing permissions
- Network issues

**Fix:**
```bash
# Restart bot
docker compose restart discord-bot

# Check token
docker compose exec discord-bot printenv DISCORD_BOT_TOKEN
```

### Service Won't Start

**Check why:**
```bash
docker compose ps  # See status
docker compose logs service-name  # See error
```

**Common causes:**
- Port already in use
- Missing environment variables
- Database connection failed

**Fix:**
```bash
# Rebuild
docker compose down
docker compose build service-name
docker compose up -d
```

### High Memory Usage

**Check:**
```bash
free -h  # System memory
docker stats --no-stream  # Container memory
```

**Fix:**
```bash
# Restart services
docker compose restart

# Or add memory limits to docker-compose.yml:
services:
  discord-bot:
    mem_limit: 512m
```

### Disk Space Full

**Check:**
```bash
df -h  # Disk usage
docker system df  # Docker disk usage
```

**Clean up:**
```bash
# Remove old images/containers
docker system prune -a

# Remove logs
sudo journalctl --vacuum-time=7d
```

---

## GitHub Actions Monitoring

### View Deployments
1. Go to GitHub repository
2. Click "Actions" tab
3. View recent workflow runs

### Deployment Failed

**Check logs in GitHub Actions:**
- Click on failed run
- Expand each step to see errors

**Common issues:**
- SSH authentication failed → Check service account permissions
- Health check timeout → Services took too long to start
- Git pull failed → Merge conflicts or permissions

**Fix:**
```bash
# SSH into VM and check manually
gcloud compute ssh alfred-prod --zone=us-central1-a
cd /opt/alfred
git status
docker compose ps
```

---

## Performance Monitoring

### Response Times
```bash
# Test AI Core Service
time curl http://localhost:8001/health

# Test Task Service
time curl http://localhost:8002/health
```

### Database Queries
Check Supabase dashboard for slow queries:
1. Go to Supabase project
2. Click "Database" → "Query Performance"

### API Rate Limits
- **ClickUp**: 100 requests/minute
- **Anthropic**: Check dashboard
- **Google APIs**: Check GCP quotas

---

## Alerting (Optional)

### Email Alerts on Failure
Add to docker-compose.yml:
```yaml
services:
  discord-bot:
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import discord"]
      interval: 60s
      timeout: 10s
      retries: 3
```

### Discord Webhook Alerts
Add webhook URL to send alerts to Discord channel when services fail.

---

## Monitoring Script

Create `/opt/alfred/monitor.sh`:
```bash
#!/bin/bash

echo "=== Alfred Health Check ==="
echo "Time: $(date)"
echo ""

echo "=== Container Status ==="
docker compose ps
echo ""

echo "=== Health Checks ==="
AI_HEALTH=$(curl -s http://localhost:8001/health)
TASK_HEALTH=$(curl -s http://localhost:8002/health)

if [[ $AI_HEALTH == *"healthy"* ]]; then
    echo "✅ AI Core Service: OK"
else
    echo "❌ AI Core Service: FAILED"
fi

if [[ $TASK_HEALTH == *"healthy"* ]]; then
    echo "✅ Task Service: OK"
else
    echo "❌ Task Service: FAILED"
fi

echo ""
echo "=== Disk Usage ==="
df -h / | grep -v tmpfs

echo ""
echo "=== Memory ==="
free -h

echo ""
echo "=== Recent Errors ==="
docker compose logs --tail=20 | grep -i error || echo "No recent errors"
```

Run:
```bash
chmod +x /opt/alfred/monitor.sh
./monitor.sh
```

Add to cron for automated checks:
```bash
# Run every hour
0 * * * * /opt/alfred/monitor.sh >> /var/log/alfred-health.log 2>&1
```

---

## Troubleshooting Checklist

- [ ] Services running (`docker compose ps`)
- [ ] Health endpoints responding
- [ ] Discord bot online in Discord
- [ ] No errors in logs
- [ ] Disk space available (`df -h`)
- [ ] Memory available (`free -h`)
- [ ] Environment variables set
- [ ] Database accessible
- [ ] External APIs reachable (ClickUp, Anthropic, Google)

---

## Next Steps

- [Deploy Updates](CI_CD_SETUP.md)
- [Database Setup](DATABASE_SETUP.md)
- [Manual Deployment](MANUAL_DEPLOYMENT.md)
