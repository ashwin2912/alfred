# Alfred Discord Bot - GCP Deployment Guide

Complete guide to deploying the Alfred Discord bot to Google Cloud Platform for production use.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Options](#deployment-options)
4. [Option 1: Cloud Run (Recommended)](#option-1-cloud-run-recommended)
5. [Option 2: Compute Engine VM](#option-2-compute-engine-vm)
6. [Option 3: Google Kubernetes Engine (GKE)](#option-3-google-kubernetes-engine-gke)
7. [Post-Deployment](#post-deployment)
8. [Monitoring & Logging](#monitoring--logging)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Alfred is a long-running Discord bot that needs to:
- Maintain persistent WebSocket connection to Discord
- Handle real-time events (onboarding, commands, etc.)
- Access external APIs (Supabase, Google Drive, ClickUp)
- Store minimal state (all data in Supabase)

**Recommended**: Cloud Run or Compute Engine VM for simplicity and cost-effectiveness.

---

## Prerequisites

### Required Services

1. **Google Cloud Platform Account**
   - Billing enabled
   - Project created

2. **External Services**
   - Supabase project (database + auth)
   - Discord bot token
   - Google Workspace with service account
   - ClickUp workspace (optional)

3. **Local Setup Complete**
   - Bot tested locally
   - All environment variables configured
   - Database migrations applied

### Required Files

```
discord-bot/
├── .env                    # Environment variables (DO NOT COMMIT)
├── requirements.txt        # Python dependencies
├── bot/                    # Bot source code
├── run.sh                 # Startup script
└── credentials/
    └── google-credentials.json  # Google service account
```

---

## Deployment Options

| Option | Best For | Pros | Cons | Cost (est.) |
|--------|----------|------|------|-------------|
| **Cloud Run** | Simple deployments | Easy setup, auto-scaling, minimal ops | WebSocket limitations | $5-15/month |
| **Compute Engine** | Production | Full control, reliable WebSocket | Manual management | $10-30/month |
| **GKE** | Large scale | Enterprise features, scaling | Complex, expensive | $70+/month |

**Recommendation**: Start with **Cloud Run** for testing, move to **Compute Engine** for production.

---

## Option 1: Cloud Run (Recommended)

### Step 1: Prepare Docker Container

Create `discord-bot/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot/ ./bot/
COPY run.sh .
RUN chmod +x run.sh

# Copy credentials (will be overridden by Secret Manager)
COPY credentials/ ./credentials/

# Set environment variables (will be overridden)
ENV PYTHONUNBUFFERED=1

# Run bot
CMD ["./run.sh"]
```

Create `discord-bot/.dockerignore`:

```
.env
.venv/
__pycache__/
*.pyc
.git/
.gitignore
*.md
tests/
```

### Step 2: Build and Push Container

```bash
# Set your GCP project ID
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com

# Build container
cd discord-bot
gcloud builds submit --tag gcr.io/$PROJECT_ID/alfred-bot

# Or use Docker locally
docker build -t gcr.io/$PROJECT_ID/alfred-bot .
docker push gcr.io/$PROJECT_ID/alfred-bot
```

### Step 3: Create Secrets

```bash
# Create secrets for sensitive data
gcloud secrets create discord-bot-token \
    --data-file=<(echo -n "YOUR_DISCORD_TOKEN")

gcloud secrets create supabase-url \
    --data-file=<(echo -n "YOUR_SUPABASE_URL")

gcloud secrets create supabase-key \
    --data-file=<(echo -n "YOUR_SUPABASE_KEY")

gcloud secrets create google-credentials \
    --data-file=credentials/google-credentials.json

# Add more secrets as needed from your .env
```

### Step 4: Deploy to Cloud Run

```bash
gcloud run deploy alfred-bot \
    --image gcr.io/$PROJECT_ID/alfred-bot \
    --region $REGION \
    --platform managed \
    --no-allow-unauthenticated \
    --min-instances 1 \
    --max-instances 1 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 3600 \
    --set-env-vars "DISCORD_GUILD_ID=YOUR_GUILD_ID,DISCORD_ADMIN_CHANNEL_ID=YOUR_ADMIN_CHANNEL,DISCORD_ALFRED_CHANNEL_ID=YOUR_ALFRED_CHANNEL" \
    --set-secrets "DISCORD_BOT_TOKEN=discord-bot-token:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_SERVICE_KEY=supabase-key:latest,GOOGLE_CREDENTIALS_PATH=/secrets/google-credentials" \
    --update-secrets "/secrets/google-credentials=google-credentials:latest"
```

**Important**: Cloud Run has WebSocket timeout limitations (1 hour). Discord bot may disconnect. Consider Compute Engine for production.

---

## Option 2: Compute Engine VM (Production Recommended)

### Step 1: Create VM Instance

```bash
gcloud compute instances create alfred-bot-vm \
    --zone=us-central1-a \
    --machine-type=e2-micro \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=10GB \
    --tags=alfred-bot \
    --metadata-from-file startup-script=startup.sh
```

### Step 2: Setup Script

Create `startup.sh`:

```bash
#!/bin/bash

# Update system
apt-get update
apt-get upgrade -y

# Install Python 3.11
apt-get install -y python3.11 python3.11-venv python3-pip git

# Create app user
useradd -m -s /bin/bash alfredbot
cd /home/alfredbot

# Clone repository (or copy files)
# git clone https://github.com/your-org/alfred.git
# OR upload via SCP/gcloud

# Setup Python environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
cd /home/alfredbot/alfred/discord-bot
pip install -r requirements.txt

# Create systemd service
cat > /etc/systemd/system/alfred-bot.service <<EOF
[Unit]
Description=Alfred Discord Bot
After=network.target

[Service]
Type=simple
User=alfredbot
WorkingDirectory=/home/alfredbot/alfred/discord-bot
Environment="PATH=/home/alfredbot/venv/bin"
EnvironmentFile=/home/alfredbot/.env
ExecStart=/home/alfredbot/venv/bin/python -m bot.bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable alfred-bot
systemctl start alfred-bot
```

### Step 3: Upload Environment Variables

Create `.env` file on VM:

```bash
# SSH into VM
gcloud compute ssh alfred-bot-vm --zone=us-central1-a

# Create .env file
sudo -u alfredbot nano /home/alfredbot/.env
```

Paste your environment variables:

```bash
# Discord
DISCORD_BOT_TOKEN=your_token_here
DISCORD_GUILD_ID=123456789
DISCORD_ADMIN_CHANNEL_ID=123456789
DISCORD_ALFRED_CHANNEL_ID=123456789

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_key_here

# Google
GOOGLE_CREDENTIALS_PATH=/home/alfredbot/credentials/google-credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
GOOGLE_DELEGATED_USER_EMAIL=admin@yourdomain.com

# ... other variables
```

### Step 4: Upload Code and Credentials

```bash
# From local machine
gcloud compute scp --recurse discord-bot/ alfred-bot-vm:/home/alfredbot/alfred/ --zone=us-central1-a

# Upload credentials
gcloud compute scp credentials/google-credentials.json alfred-bot-vm:/home/alfredbot/credentials/ --zone=us-central1-a

# Set permissions
gcloud compute ssh alfred-bot-vm --zone=us-central1-a --command="sudo chown -R alfredbot:alfredbot /home/alfredbot/alfred"
```

### Step 5: Start the Bot

```bash
# SSH into VM
gcloud compute ssh alfred-bot-vm --zone=us-central1-a

# Start service
sudo systemctl start alfred-bot

# Check status
sudo systemctl status alfred-bot

# View logs
sudo journalctl -u alfred-bot -f
```

---

## Option 3: Google Kubernetes Engine (GKE)

For enterprise deployments with high availability requirements.

### Step 1: Create GKE Cluster

```bash
gcloud container clusters create alfred-cluster \
    --zone us-central1-a \
    --num-nodes 2 \
    --machine-type e2-small \
    --enable-autoscaling \
    --min-nodes 1 \
    --max-nodes 3
```

### Step 2: Create Kubernetes Resources

`k8s/deployment.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: alfred-secrets
type: Opaque
stringData:
  DISCORD_BOT_TOKEN: "your_token"
  SUPABASE_URL: "your_url"
  SUPABASE_SERVICE_KEY: "your_key"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alfred-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: alfred-bot
  template:
    metadata:
      labels:
        app: alfred-bot
    spec:
      containers:
      - name: bot
        image: gcr.io/PROJECT_ID/alfred-bot:latest
        envFrom:
        - secretRef:
            name: alfred-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Step 3: Deploy

```bash
kubectl apply -f k8s/deployment.yaml
kubectl get pods
kubectl logs -f deployment/alfred-bot
```

---

## Post-Deployment

### 1. Verify Bot is Online

- Check Discord server - bot should show as online
- Run `/help` command to verify
- Check logs for any errors

### 2. Test Core Functionality

```bash
# In Discord
/start-onboarding    # Test onboarding flow
/create-team         # Test team creation (admin)
/my-tasks           # Test ClickUp integration
```

### 3. Setup Monitoring

Enable Cloud Logging:

```bash
gcloud logging read "resource.type=cloud_run_revision" --limit 50
# OR for Compute Engine
gcloud compute ssh alfred-bot-vm --command="sudo journalctl -u alfred-bot -f"
```

### 4. Setup Alerts

Create uptime check:

```bash
# For Cloud Run
gcloud monitoring uptime-checks create http alfred-bot-uptime \
    --display-name="Alfred Bot Health" \
    --uri=https://alfred-bot-xxx.run.app/health

# For VM - use Discord API to check bot status
```

---

## Monitoring & Logging

### View Logs

**Cloud Run**:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=alfred-bot" --limit 50 --format json
```

**Compute Engine**:
```bash
gcloud compute ssh alfred-bot-vm --command="sudo journalctl -u alfred-bot -f"
```

**Cloud Console**: Navigation > Logging > Logs Explorer

### Key Metrics to Monitor

1. **Bot Uptime**: Discord connection status
2. **Error Rate**: Count of exceptions in logs
3. **Command Latency**: Response times for commands
4. **API Quota**: Google Drive/ClickUp API usage
5. **Memory Usage**: Prevent OOM kills

### Setup Alerts

```bash
# Create alert for high error rate
gcloud alpha monitoring policies create \
    --notification-channels=YOUR_CHANNEL_ID \
    --display-name="Alfred Bot High Error Rate" \
    --condition-display-name="Error rate > 10/min" \
    --condition-threshold-value=10 \
    --condition-threshold-duration=60s
```

---

## Troubleshooting

### Bot Won't Start

```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision" --limit 10

# Common issues:
# 1. Missing environment variables
# 2. Invalid Discord token
# 3. Supabase connection failure
# 4. Google credentials not found
```

### Bot Disconnects Frequently

**Cloud Run**: WebSocket timeout - migrate to Compute Engine
**Compute Engine**: Check network connectivity, restart service

```bash
sudo systemctl restart alfred-bot
```

### Commands Not Working

1. Check bot permissions in Discord
2. Verify slash commands are synced: Check bot logs for "Synced commands"
3. Re-sync if needed (restart bot)

### Database Errors

```bash
# Check Supabase connection
curl -H "apikey: YOUR_KEY" https://your-project.supabase.co/rest/v1/teams

# Verify migrations applied
# Run missing migrations via Supabase Dashboard > SQL Editor
```

### Google Drive Errors

1. Verify service account has domain-wide delegation
2. Check credentials file path
3. Ensure delegated user email is correct
4. Verify folder permissions

---

## Cost Optimization

### Cloud Run
- Use `--min-instances 1` to keep bot alive
- Monitor CPU/memory usage, reduce if possible
- Estimated: $5-15/month

### Compute Engine
- Use `e2-micro` for small servers (<100 members)
- Use preemptible instances for testing ($1-2/month)
- Shutdown during off-hours if acceptable
- Estimated: $5-10/month (e2-micro), $10-30/month (e2-small)

### GKE
- Not cost-effective for single bot
- Only use if running multiple services
- Estimated: $70+/month

---

## Security Best Practices

1. **Never commit secrets** to git
2. **Use Secret Manager** for production
3. **Restrict VM SSH** to specific IPs
4. **Enable VPC firewall rules**
5. **Regular security updates**: `apt-get update && apt-get upgrade`
6. **Rotate credentials** every 90 days
7. **Monitor access logs**

---

## Maintenance

### Update Bot Code

**Cloud Run**:
```bash
# Rebuild and redeploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/alfred-bot
gcloud run deploy alfred-bot --image gcr.io/$PROJECT_ID/alfred-bot
```

**Compute Engine**:
```bash
# SSH and pull updates
gcloud compute ssh alfred-bot-vm
cd /home/alfredbot/alfred
git pull
sudo systemctl restart alfred-bot
```

### Database Migrations

Apply via Supabase Dashboard SQL Editor or:

```bash
# SSH to VM
gcloud compute ssh alfred-bot-vm
psql "your_supabase_connection_string" -f migration.sql
```

### Backup Strategy

- **Database**: Supabase auto-backups enabled
- **Google Drive**: Files owned by service account
- **Bot config**: .env file backed up to Secret Manager
- **Code**: Git repository

---

## Quick Start Checklist

- [ ] GCP project created with billing enabled
- [ ] APIs enabled (Compute/Run, Container Registry, Secret Manager)
- [ ] Bot tested locally
- [ ] Environment variables documented
- [ ] Database migrations applied
- [ ] Choose deployment option (Cloud Run vs VM)
- [ ] Create secrets in Secret Manager
- [ ] Deploy bot
- [ ] Verify bot online in Discord
- [ ] Test core commands
- [ ] Setup monitoring and alerts
- [ ] Document access and credentials

---

**Recommended Path**:
1. Start with **Cloud Run** for quick testing
2. Monitor for WebSocket disconnects
3. Migrate to **Compute Engine VM** if issues persist
4. Use **e2-micro** instance for cost optimization
5. Scale up to e2-small if performance needed

**Need Help?** Check logs, Discord server status, and Supabase dashboard first.

---

**Last Updated**: Dec 14, 2024  
**Status**: Production-ready deployment guide  
**Recommended**: Compute Engine VM (e2-micro) for reliability
