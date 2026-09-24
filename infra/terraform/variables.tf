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
# Pass whichever provider you are deploying on. At least one is required: with neither, the service
# still serves every endpoint on the keyword rules alone, which is a legitimate mode but almost
# certainly not what you meant by deploying it.
variable "anthropic_api_key" {
  type      = string
  sensitive = true
  default   = ""
}
variable "openai_api_key" {
  type      = string
  sensitive = true
  default   = ""
}
variable "llm_provider" {
  type        = string
  default     = "auto"
  description = "auto | anthropic | openai. auto prefers Anthropic when both keys are set."
  validation {
    condition     = contains(["auto", "anthropic", "openai"], var.llm_provider)
    error_message = "llm_provider must be auto, anthropic, or openai."
  }
}
variable "claude_model" {
  type    = string
  default = "claude-opus-5"
}
variable "openai_model" {
  type    = string
  default = "gpt-5"
}
variable "openai_reasoning_effort" {
  type        = string
  default     = "low"
  description = "minimal | low | medium | high. The dominant cost lever on the OpenAI path."
}
variable "public" {
  type        = bool
  default     = true
  description = "Allow unauthenticated invocations (demo). Set false and front with IAP for real traffic."
}
