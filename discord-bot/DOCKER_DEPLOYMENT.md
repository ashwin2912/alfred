# Docker Deployment Guide

## Local Testing

### 1. Build Image
```bash
cd /path/to/alfred
docker build -f discord-bot/Dockerfile -t alfred-bot .
```

### 2. Run Container
```bash
docker run -d \
  --name alfred-bot \
  --env-file discord-bot/.env \
  -v $(pwd)/discord-bot/credentials:/app/credentials:ro \
  --restart unless-stopped \
  alfred-bot
```

### 3. View Logs
```bash
docker logs -f alfred-bot
```

### 4. Stop/Remove
```bash
docker stop alfred-bot
docker rm alfred-bot
```

## Docker Compose (Easier)

### Run
```bash
cd /path/to/alfred
docker-compose up -d
```

### Logs
```bash
docker-compose logs -f alfred-bot
```

### Stop
```bash
docker-compose down
```

### Rebuild After Code Changes
```bash
docker-compose build
docker-compose up -d
```

---

## GCP Compute Engine Deployment

### Step 1: Create VM
```bash
gcloud compute instances create alfred-bot-vm \
    --zone=us-central1-a \
    --machine-type=e2-micro \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=10GB \
    --tags=alfred-bot \
    --metadata=startup-script='#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose
systemctl enable docker
systemctl start docker
usermod -aG docker $USER'
```

### Step 2: Upload Project
```bash
# From local machine
cd /Users/ashwindhanasamy/Documents/cave/projects/alfred/alfred

# Create tar (excludes venv, git)
tar -czf alfred.tar.gz \
    --exclude='.git' \
    --exclude='*/.venv' \
    --exclude='**/__pycache__' \
    --exclude='*.pyc' \
    discord-bot/ shared-services/ docker-compose.yml

# Upload to VM
gcloud compute scp alfred.tar.gz alfred-bot-vm:/home/$USER/ --zone=us-central1-a

# Upload .env separately (NEVER commit)
gcloud compute scp discord-bot/.env alfred-bot-vm:/home/$USER/ --zone=us-central1-a

# Upload credentials
gcloud compute scp discord-bot/credentials/google-credentials.json alfred-bot-vm:/home/$USER/ --zone=us-central1-a
```

### Step 3: Setup on VM
```bash
# SSH into VM
gcloud compute ssh alfred-bot-vm --zone=us-central1-a

# Extract
mkdir -p alfred
cd alfred
tar -xzf ../alfred.tar.gz

# Move .env and credentials
mv ../.env discord-bot/
mkdir -p discord-bot/credentials
mv ../google-credentials.json discord-bot/credentials/

# Build and run
docker-compose build
docker-compose up -d

# Check logs
docker-compose logs -f alfred-bot
```

### Step 4: Auto-start on Boot
```bash
# On VM, create systemd service
sudo nano /etc/systemd/system/alfred-docker.service
```

Paste:
```ini
[Unit]
Description=Alfred Discord Bot Docker
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/YOUR_USERNAME/alfred
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=YOUR_USERNAME

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable alfred-docker
```

---

## Updating the Bot

### On VM:
```bash
# SSH in
gcloud compute ssh alfred-bot-vm --zone=us-central1-a

cd alfred

# Pull new code (if using git)
git pull

# Or upload new tar from local machine, then:
# tar -xzf ../alfred.tar.gz

# Rebuild and restart
docker-compose build
docker-compose up -d

# Verify
docker-compose logs -f alfred-bot
```

---

## Troubleshooting

### Check Container Status
```bash
docker ps -a
```

### Enter Running Container
```bash
docker exec -it alfred-bot bash
```

### View Resource Usage
```bash
docker stats alfred-bot
```

### Container Won't Start
```bash
# Check logs
docker logs alfred-bot

# Common issues:
# - Missing .env file
# - Missing credentials file
# - Port already in use
# - Invalid environment variables
```

### Rebuild from Scratch
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Cost Estimate

- **e2-micro VM**: ~$7/month
- **Disk (10GB)**: ~$0.40/month
- **Network egress**: ~$1-2/month (first 1GB free)
- **Total**: ~$8-10/month

---

## Security Notes

1. **.env is in .dockerignore**: Never gets into image
2. **Credentials mounted read-only**: `:ro` flag
3. **No exposed ports**: Bot only makes outbound connections
4. **VM firewall**: Only SSH port 22 open by default

---

## Advantages of Docker

✅ **Reproducible**: Same environment everywhere  
✅ **Easy updates**: Rebuild + restart  
✅ **Isolated**: Won't break system packages  
✅ **Portable**: Move to any cloud provider  
✅ **Logs managed**: Auto-rotation built-in  
✅ **Resource limits**: Can set memory/CPU caps  

vs systemd approach:
❌ Manual Python venv setup  
❌ System dependency conflicts  
❌ Harder to reproduce issues  
❌ Log management manual  
