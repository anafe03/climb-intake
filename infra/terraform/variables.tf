variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "us-central1"
}
variable "service_name" {
  type    = string
  default = "climb-intake"
}
variable "image" {
  type        = string
  description = "Fully qualified image, e.g. us-central1-docker.pkg.dev/PROJECT/climb-intake/intake:v1"
}
variable "anthropic_api_key" {
  type      = string
  sensitive = true
}
variable "claude_model" {
  type    = string
  default = "claude-opus-5"
}
variable "public" {
  type        = bool
  default     = true
  description = "Allow unauthenticated invocations (demo). Set false and front with IAP for real traffic."
}
