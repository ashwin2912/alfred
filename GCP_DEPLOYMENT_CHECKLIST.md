# GCP Deployment Checklist

Quick reference guide for deploying Alfred bot to GCP VM.

## Pre-Deployment Validation

### 1. Verify Local Environment
```bash
# Run automated verification
./scripts/verify_setup.sh

# Manual checks if needed:
docker --version  # Should be 20.10+
docker compose version  # Should be 2.0+
```

### 2. Check Required Files
- [ ] `discord-bot/.env` configured with all values
- [ ] `discord-bot/credentials/google-credentials.json` present
- [ ] Database migrations applied to Supabase
- [ ] Discord bot token valid and bot invited to server

### 3. Test Local Build
```bash
# Build and test locally first
docker compose build
docker compose up

# Verify bot comes online in Discord
# Test basic commands: /help, /start-onboarding
# Stop with Ctrl+C
```

## GCP VM Setup

### 1. Create VM Instance
```bash
# Option A: Using gcloud CLI (recommended)
gcloud compute instances create alfred-bot \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=10GB \
  --boot-disk-type=pd-standard \
  --tags=alfred-bot

# Option B: Use GCP Console
# 1. Go to Compute Engine > VM Instances
# 2. Click "Create Instance"
# 3. Name: alfred-bot
# 4. Region: us-central1, Zone: us-central1-a
# 5. Machine type: e2-micro (2 vCPU, 1 GB memory)
# 6. Boot disk: Ubuntu 22.04 LTS, 10 GB
# 7. Click "Create"
```

### 2. Connect to VM
```bash
gcloud compute ssh alfred-bot --zone=us-central1-a

# Or use SSH button in GCP Console
```

### 3. Install Docker on VM
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (avoid sudo)
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install -y docker-compose-plugin

# Log out and back in for group changes
exit
gcloud compute ssh alfred-bot --zone=us-central1-a

# Verify installation
docker --version
docker compose version
```

## Deploy Application

### 1. Transfer Files to VM
```bash
# From your LOCAL machine (not VM):
# Create deployment package (excludes venv, cache, etc.)
cd /Users/ashwindhanasamy/Documents/cave/projects/alfred/alfred
tar -czf alfred-deploy.tar.gz \
  --exclude='**/venv' \
  --exclude='**/__pycache__' \
  --exclude='**/.pytest_cache' \
  --exclude='**/node_modules' \
  --exclude='.git' \
  discord-bot/ shared-services/ docker-compose.yml

# Copy to VM
gcloud compute scp alfred-deploy.tar.gz alfred-bot:~ --zone=us-central1-a

# SSH back into VM
gcloud compute ssh alfred-bot --zone=us-central1-a

# Extract files
tar -xzf alfred-deploy.tar.gz
cd ~/
```

### 2. Set Up Environment
```bash
# Create credentials directory
mkdir -p discord-bot/credentials

# Copy your .env and credentials
# Method 1: Use SCP from local machine
# gcloud compute scp discord-bot/.env alfred-bot:~/discord-bot/.env --zone=us-central1-a
# gcloud compute scp discord-bot/credentials/google-credentials.json alfred-bot:~/discord-bot/credentials/ --zone=us-central1-a

# Method 2: Create files manually on VM
nano discord-bot/.env  # Paste contents, Ctrl+X to save
nano discord-bot/credentials/google-credentials.json  # Paste JSON, Ctrl+X to save

# Verify files
ls -la discord-bot/.env
ls -la discord-bot/credentials/google-credentials.json
```

### 3. Build and Start Bot
```bash
# Build Docker image
docker compose build

# Start bot in detached mode
docker compose up -d

# Verify container is running
docker compose ps
```

### 4. Monitor Logs
```bash
# Watch live logs
docker compose logs -f

# Check for successful startup:
# ✓ "Logged in as Alfred Bot"
# ✓ "Ready to serve"
# ✓ No error messages about missing env vars or credentials

# Exit logs with Ctrl+C (bot keeps running)
```

## Post-Deployment Verification

### 1. Discord Bot Status
- [ ] Bot shows as "Online" in Discord server
- [ ] Bot responds to `/help` command
- [ ] Bot can create test channel with `/create-team test-team`

### 2. Integration Tests
```bash
# Test each integration by running commands:

# ClickUp Integration
/setup-clickup  # Paste your ClickUp API token

# Google Drive Integration  
/start-onboarding  # Create test profile
# Check Google Drive for new document

# Supabase Database
# Run SQL query to verify data:
# SELECT * FROM teams LIMIT 5;
```

### 3. Background Operations
- [ ] Main roster auto-created in Google Drive
- [ ] Profile documents created successfully
- [ ] Team folders accessible
- [ ] Database writes successful

## Common Issues & Fixes

### Bot Won't Start
```bash
# Check logs for specific error
docker compose logs alfred-bot

# Common fixes:
# 1. Missing environment variable
docker compose down
nano discord-bot/.env  # Add missing variable
docker compose up -d

# 2. Invalid credentials
cat discord-bot/credentials/google-credentials.json  # Verify JSON is valid
docker compose restart

# 3. Build failed
docker compose build --no-cache
docker compose up -d
```

### Container Keeps Restarting
```bash
# View crash logs
docker compose logs --tail=50 alfred-bot

# Check container status
docker compose ps

# Common causes:
# - Invalid Discord token
# - Supabase connection refused (check SUPABASE_URL and key)
# - Missing Google credentials file
```

### Commands Not Responding
```bash
# Ensure bot has proper Discord permissions:
# - Send Messages
# - Embed Links
# - Manage Channels
# - Manage Roles
# - Use Slash Commands

# Re-sync slash commands (if needed):
docker compose exec alfred-bot python -c "
from bot.bot import bot
bot.tree.sync()
"
```

### Database Connection Issues
```bash
# Test Supabase connection
curl -H "apikey: YOUR_SUPABASE_KEY" \
     https://YOUR_PROJECT.supabase.co/rest/v1/teams

# Verify .env has correct values:
# SUPABASE_URL=https://YOUR_PROJECT.supabase.co
# SUPABASE_SERVICE_KEY=your_service_role_key
```

### Google Drive Permission Denied
```bash
# Verify service account has domain-wide delegation
# Verify GOOGLE_DELEGATED_USER_EMAIL is correct
# Check credentials file is valid JSON

# Test credentials manually:
docker compose exec alfred-bot python -c "
from google.oauth2 import service_account
creds = service_account.Credentials.from_service_account_file(
    '/app/credentials/google-credentials.json'
)
print('Credentials valid:', creds.service_account_email)
"
```

## Ongoing Operations

### View Logs
```bash
# Real-time logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100

# Specific time range
docker compose logs --since="2024-01-01T12:00:00"
```

### Update Bot Code
```bash
# From local machine, create new deployment package
cd /Users/ashwindhanasamy/Documents/cave/projects/alfred/alfred
tar -czf alfred-deploy.tar.gz \
  --exclude='**/venv' \
  --exclude='**/__pycache__' \
  discord-bot/ shared-services/ docker-compose.yml

# Copy to VM
gcloud compute scp alfred-deploy.tar.gz alfred-bot:~ --zone=us-central1-a

# On VM:
docker compose down
rm -rf discord-bot/ shared-services/ docker-compose.yml
tar -xzf alfred-deploy.tar.gz
docker compose build
docker compose up -d
```

### Restart Bot
```bash
# Graceful restart
docker compose restart

# Full rebuild
docker compose down
docker compose up -d --build
```

### Stop Bot
```bash
# Stop container (keeps data)
docker compose down

# Stop and remove all data
docker compose down -v
```

## Cost Monitoring

### Expected Monthly Cost (e2-micro)
- VM: ~$7/month (730 hours)
- Disk: ~$0.40/month (10 GB standard)
- Network: Minimal (most traffic is outbound - free)
- **Total: ~$7-8/month**

### View Current Usage
```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Check Docker resource usage
docker stats
```

## Security Checklist

- [ ] `.env` file not committed to git
- [ ] `google-credentials.json` not committed to git
- [ ] Supabase service role key not exposed publicly
- [ ] Discord bot token regenerated if ever exposed
- [ ] VM firewall only allows outbound connections
- [ ] Regular system updates: `sudo apt-get update && sudo apt-get upgrade`

## Quick Reference Commands

```bash
# SSH to VM
gcloud compute ssh alfred-bot --zone=us-central1-a

# Start bot
docker compose up -d

# Stop bot
docker compose down

# View logs
docker compose logs -f

# Restart bot
docker compose restart

# Rebuild and restart
docker compose up -d --build

# Shell into container
docker compose exec alfred-bot bash

# Check container status
docker compose ps
```

---

**Next Steps After Deployment:**
1. Test all slash commands in Discord
2. Complete a full onboarding flow with a test user
3. Verify Google Drive permissions work automatically
4. Test ClickUp integration with real tasks
5. Monitor logs for 24-48 hours to catch any edge cases
6. Consider implementing ACTION_REQUEST_SYSTEM_PLAN.md once stable
