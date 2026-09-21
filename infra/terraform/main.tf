resource "google_project_service" "apis" {
  for_each = toset(["run.googleapis.com", "artifactregistry.googleapis.com", "secretmanager.googleapis.com"])
  service  = each.key
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.service_name
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

resource "google_secret_manager_secret" "anthropic" {
  secret_id = "${var.service_name}-anthropic-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "anthropic" {
  secret      = google_secret_manager_secret.anthropic.id
  secret_data = var.anthropic_api_key
}

resource "google_service_account" "svc" {
  account_id   = "${var.service_name}-sa"
  display_name = "Climb intake service"
}

resource "google_secret_manager_secret_iam_member" "svc_reads_key" {
  secret_id = google_secret_manager_secret.anthropic.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.svc.email}"
}

resource "google_cloud_run_v2_service" "intake" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.svc.email
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
    containers {
      image = var.image
      ports { container_port = 8080 }
      resources {
        limits = { cpu = "1", memory = "512Mi" }
      }
      env {
        name  = "CLASSIFIER_MODE"
        value = "auto"
      }
      env {
        name  = "CLAUDE_MODEL"
        value = var.claude_model
      }
      env {
        name  = "AUDIT_DB_PATH"
        value = "/srv/data/audit.db"
      }
      env {
        name = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.anthropic.secret_id
            version = "latest"
          }
        }
      }
      # Demo tier: in-memory volume so the audit DB survives across requests within an instance.
      # Scale path: Cloud SQL behind app/audit.py.
      volume_mounts {
        name       = "data"
        mount_path = "/srv/data"
      }
      startup_probe {
        http_get { path = "/health" }
        initial_delay_seconds = 2
        period_seconds        = 3
        failure_threshold     = 10
      }
      liveness_probe {
        http_get { path = "/health" }
        period_seconds = 30
      }
    }
    volumes {
      name = "data"
      empty_dir {
        medium     = "MEMORY"
        size_limit = "128Mi"
      }
    }
  }

  depends_on = [google_secret_manager_secret_iam_member.svc_reads_key, google_project_service.apis]
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.public ? 1 : 0
  name     = google_cloud_run_v2_service.intake.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
