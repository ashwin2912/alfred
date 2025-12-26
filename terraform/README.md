# Terraform Deployment for Alfred

## Quick Deploy

```bash
# 1. Install Terraform
brew install terraform  # macOS
# or download from: https://www.terraform.io/downloads

# 2. Configure
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your GCP project ID

# 3. Initialize
terraform init

# 4. Plan (preview changes)
terraform plan

# 5. Deploy
terraform apply

# 6. SSH into instance
terraform output -raw ssh_command | bash

# 7. Deploy Alfred
cd alfred
git clone <your-repo>
cd alfred
cp .env.example .env
nano .env  # Configure
./deploy.sh
```

## Outputs

After `terraform apply`, you'll get:
- Instance name
- External IP
- SSH command
- Service URLs

## Destroy

```bash
terraform destroy
```

## State Management

For team collaboration, use remote state:

```hcl
# backend.tf
terraform {
  backend "gcs" {
    bucket = "your-terraform-state-bucket"
    prefix = "alfred/prod"
  }
}
```
