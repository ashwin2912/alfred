# GitHub Actions CI/CD Setup

## Overview
Automated deployment to GCP VM on every push to `main` branch.

---

## Prerequisites

1. GCP VM already set up (see MANUAL_DEPLOYMENT.md)
2. GitHub repository
3. GCP service account with permissions

---

## Setup Steps

### 1. Create GCP Service Account

```bash
# Set your project ID
PROJECT_ID="your-project-id"

# Create service account
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions Deployer" \
    --project=${PROJECT_ID}

# Grant necessary permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/compute.instanceAdmin.v1"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com
```

### 2. Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

1. **GCP_SA_KEY**
   ```bash
   # Copy the contents of github-actions-key.json
   cat github-actions-key.json | pbcopy  # macOS
   cat github-actions-key.json | xclip   # Linux
   ```
   Paste the entire JSON content as the secret value.

2. **GCP_PROJECT_ID**
   ```
   your-project-id
   ```

### 3. Configure SSH Access for Service Account

On your GCP VM:

```bash
# SSH into your VM
gcloud compute ssh alfred-prod --zone=us-central1-a

# The service account needs to be able to SSH
# This is automatically handled by gcloud compute ssh
# No additional setup needed
```

### 4. Initial Git Setup on VM

```bash
# SSH into VM
gcloud compute ssh alfred-prod --zone=us-central1-a

# Navigate to project
cd ~/alfred

# Ensure git is configured
git config pull.rebase false

# Ensure main branch is tracking remote
git branch --set-upstream-to=origin/main main
```

### 5. Push to Trigger Deployment

```bash
# On your local machine
git add .
git commit -m "Setup CI/CD"
git push origin main
```

Watch the deployment in GitHub Actions tab.

---

## Workflow Details

### When it runs
- Automatically on push to `main` branch
- Manually via "Run workflow" button in GitHub Actions

### What it does
1. Checks out code
2. Sets up Google Cloud SDK
3. SSHs into GCP VM
4. Pulls latest code
5. Runs `deployment/deploy.sh`
6. Verifies services are healthy

### Deployment script does
1. Pulls latest changes
2. Builds Docker images
3. Stops old containers
4. Starts new containers
5. Health checks all services
6. Shows logs if anything fails

---

## Monitoring Deployments

### View in GitHub
1. Go to your repository
2. Click "Actions" tab
3. Click on latest workflow run
4. View logs for each step

### View on VM
```bash
# SSH into VM
gcloud compute ssh alfred-prod --zone=us-central1-a

# Check service status
cd ~/alfred
docker compose ps

# View logs
docker compose logs -f
```

---

## Troubleshooting

### Deployment fails at SSH step

**Issue:** Permission denied or connection refused

**Solution:**
```bash
# Ensure VM is running
gcloud compute instances list

# Start if stopped
gcloud compute instances start alfred-prod --zone=us-central1-a

# Test SSH manually
gcloud compute ssh alfred-prod --zone=us-central1-a
```

### Health check fails

**Issue:** Services don't respond to health checks

**Solution:**
```bash
# SSH into VM
gcloud compute ssh alfred-prod --zone=us-central1-a

# Check what's wrong
cd ~/alfred
docker compose logs

# Check if services are actually running
docker compose ps

# Restart services
docker compose restart
```

### Git pull fails

**Issue:** Merge conflicts or uncommitted changes

**Solution:**
```bash
# SSH into VM
gcloud compute ssh alfred-prod --zone=us-central1-a

cd ~/alfred

# See what's different
git status

# If you have local changes you want to keep
git stash
git pull
git stash pop

# If you want to discard local changes
git reset --hard origin/main
git pull
```

### Service account permissions

**Issue:** "Permission denied" in GitHub Actions

**Solution:**
```bash
# Re-grant permissions
PROJECT_ID="your-project-id"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/compute.instanceAdmin.v1"
```

---

## Advanced: Multiple Environments

### Add staging environment

1. Create a staging VM:
   ```bash
   gcloud compute instances create alfred-staging \
       --zone=us-central1-a \
       --machine-type=e2-small \
       --image-family=ubuntu-2204-lts \
       --image-project=ubuntu-os-cloud
   ```

2. Create `.github/workflows/deploy-staging.yml`:
   ```yaml
   name: Deploy to Staging
   
   on:
     push:
       branches:
         - develop
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         # Same as deploy.yml but with:
         # GCP_VM_NAME: alfred-staging
   ```

---

## Manual Deployment (Bypass CI/CD)

If you need to deploy manually:

```bash
# SSH into VM
gcloud compute ssh alfred-prod --zone=us-central1-a

# Run deployment script
cd ~/alfred
./deployment/deploy.sh
```

---

## Rollback

### To previous commit

```bash
# SSH into VM
gcloud compute ssh alfred-prod --zone=us-central1-a

cd ~/alfred

# View recent commits
git log --oneline -5

# Rollback to specific commit
git reset --hard <commit-hash>

# Redeploy
./deployment/deploy.sh
```

### Using GitHub Actions

1. Go to Actions tab
2. Find successful previous deployment
3. Click "Re-run all jobs"

---

## Security Best Practices

1. **Rotate service account keys** every 90 days
2. **Use separate service accounts** for staging/production
3. **Never commit** `.env` files or credentials
4. **Use GCP Secret Manager** for sensitive data (advanced)
5. **Enable audit logging** for deployments

---

## Next Steps

- [ ] Set up deployment notifications (Slack/Discord)
- [ ] Add automated tests before deployment
- [ ] Configure blue-green deployments
- [ ] Set up monitoring/alerting
- [ ] Document rollback procedures
