output "url" {
  value = google_cloud_run_v2_service.intake.uri
}
output "image_repo" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}"
}
