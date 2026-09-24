resource "google_project_service" "apis" {
  for_each           = toset(["run.googleapis.com", "artifactregistry.googleapis.com", "secretmanager.googleapis.com"])
  service            = each.key
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.service_name
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

# One secret per provider, created only for the keys you actually pass. The service runs on either
# one; the demo runs OpenAI, so deploying Anthropic-only Terraform would have shipped something
# different from what was demonstrated.
locals {
  # for_each cannot take a sensitive value, and anything derived from one inherits the mark — so
  # unmark the *presence* of each key, which is not a secret, and keep the key material itself out
  # of the iterator entirely.
  present = toset(compact([
    nonsensitive(var.anthropic_api_key != "") ? "anthropic" : "",
    nonsensitive(var.openai_api_key != "") ? "openai" : "",
  ]))
  key_value = {
    anthropic = var.anthropic_api_key
    openai    = var.openai_api_key
  }
  env_name = {
    anthropic = "ANTHROPIC_API_KEY"
    openai    = "OPENAI_API_KEY"
  }
}

resource "google_secret_manager_secret" "key" {
  for_each  = local.present
  secret_id = "${var.service_name}-${each.key}-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "key" {
  for_each    = local.present
  secret      = google_secret_manager_secret.key[each.key].id
  secret_data = local.key_value[each.key]
}

resource "google_service_account" "svc" {
  account_id   = "${var.service_name}-sa"
  display_name = "Climb intake service"
}

# Scoped to the secrets this service needs and nothing else in the project.
resource "google_secret_manager_secret_iam_member" "svc_reads_key" {
  for_each  = local.present
  secret_id = google_secret_manager_secret.key[each.key].id
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
        name  = "OPENAI_MODEL"
        value = var.openai_model
      }
      # Output tokens dominate the bill on reasoning models; see docs/DECISIONS.md D54.
      env {
        name  = "OPENAI_REASONING_EFFORT"
        value = var.openai_reasoning_effort
      }
      env {
        name  = "LLM_PROVIDER"
        value = var.llm_provider
      }
      env {
        name  = "AUDIT_DB_PATH"
        value = "/srv/data/audit.db"
      }
      dynamic "env" {
        for_each = local.present
        content {
          name = local.env_name[env.value]
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.key[env.value].secret_id
              version = "latest"
            }
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
