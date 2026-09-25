#!/usr/bin/env bash
# Stand the service up on GCP Cloud Run, in the order that works from a clean project.
#   PROJECT=my-gcp-project ./scripts/deploy.sh          # deploy / redeploy with tag v1
#   PROJECT=my-gcp-project TAG=v2 ./scripts/deploy.sh   # push a new image and roll it out
# Needs gcloud (logged in, billing enabled on PROJECT), docker with buildx, and tofu or terraform.
# OPENAI_API_KEY comes from the environment, or from .env if unset there.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null || export PATH="$HOME/.local/bin:$PATH"

: "${PROJECT:?set PROJECT to your GCP project id}"
REGION=${REGION:-us-central1}
TAG=${TAG:-v1}
TF=$(command -v tofu || command -v terraform) || { echo "need tofu or terraform"; exit 1; }
if [ -z "${OPENAI_API_KEY:-}" ] && [ -f .env ]; then
  OPENAI_API_KEY=$(grep -E '^OPENAI_API_KEY=' .env | cut -d= -f2- | tr -d '"')
fi
: "${OPENAI_API_KEY:?no OPENAI_API_KEY in the environment or .env}"
IMAGE=$REGION-docker.pkg.dev/$PROJECT/climb-intake/intake:$TAG

# The key goes in through the environment, not -var, so it never shows in the process list.
export TF_VAR_openai_api_key=$OPENAI_API_KEY
VARS=(-var "project_id=$PROJECT" -var "region=$REGION" -var "image=$IMAGE" -var "llm_provider=openai")

echo "── 1/4 terraform init"
(cd infra/terraform && $TF init -input=false >/dev/null)

# The registry has to exist before the image can be pushed, and the service needs the image before
# it can start, so the registry goes first on its own.
echo "── 2/4 enable APIs + create the image registry"
(cd infra/terraform && $TF apply -input=false -auto-approve "${VARS[@]}" \
   -target=google_project_service.apis -target=google_artifact_registry_repository.repo)

# Cloud Run runs linux/amd64 only. Built on an Apple Silicon Mac without --platform, the image is
# arm64 and the revision fails to start with "exec format error". It has to be buildx: the legacy
# builder refuses to cross-build ("does not provide the specified platform").
echo "── 3/4 build linux/amd64 image and push $IMAGE"
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet >/dev/null
docker buildx build --platform linux/amd64 -t "$IMAGE" --push .

echo "── 4/4 apply the rest (secret, service account, Cloud Run, public invoker)"
(cd infra/terraform && $TF apply -input=false -auto-approve "${VARS[@]}")

URL=$(cd infra/terraform && $TF output -raw url)
echo "── checking $URL/health"
for _ in $(seq 1 30); do curl -fs "$URL/health" && echo && break; sleep 2; done
echo "deployed: $URL"
