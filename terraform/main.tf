# Terraform configuration for Alfred production deployment
# Use this for: Reproducible infrastructure, team collaboration, production-grade

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Compute Engine instance for Alfred services
resource "google_compute_instance" "alfred_prod" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = var.disk_size_gb
      type  = "pd-standard"
    }
  }

  network_interface {
    network = "default"
    access_config {
      # Ephemeral external IP
    }
  }

  metadata_startup_script = file("${path.module}/startup-script.sh")

  tags = ["alfred-server"]

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    service     = "alfred"
  }
}

# Firewall rule for HTTP/HTTPS and service ports
resource "google_compute_firewall" "alfred_http" {
  name    = "alfred-http-${var.environment}"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "8001", "8002"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["alfred-server"]

  description = "Allow HTTP/HTTPS and service ports for Alfred ${var.environment}"
}

# Static IP (optional, for production)
resource "google_compute_address" "alfred_static_ip" {
  count = var.use_static_ip ? 1 : 0

  name   = "alfred-static-ip-${var.environment}"
  region = var.region
}

# Outputs
output "instance_name" {
  value = google_compute_instance.alfred_prod.name
}

output "external_ip" {
  value = google_compute_instance.alfred_prod.network_interface[0].access_config[0].nat_ip
}

output "ssh_command" {
  value = "gcloud compute ssh ${google_compute_instance.alfred_prod.name} --zone=${var.zone}"
}

output "ai_core_service_url" {
  value = "http://${google_compute_instance.alfred_prod.network_interface[0].access_config[0].nat_ip}:8001"
}

output "task_service_url" {
  value = "http://${google_compute_instance.alfred_prod.network_interface[0].access_config[0].nat_ip}:8002"
}
