#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="docker-compose.linux.yml"
ENV_FILE=".env.linux"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required."
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  cp .env.linux.example "$ENV_FILE"
  echo "Created $ENV_FILE from example — review OCR_HOST_PORT / OCR_LANG if needed."
fi

if ! docker network inspect alterai_default >/dev/null 2>&1; then
  echo "ERROR: Docker network 'alterai_default' not found."
  echo "Start local-ai-translator (or create the network) first, then retry."
  echo "  docker network ls | grep alterai"
  exit 1
fi

WITH_UI=0
for arg in "$@"; do
  if [[ "$arg" == "--ui" ]]; then
    WITH_UI=1
  fi
done

echo "Building and starting OCR App (CPU-only) on network alterai_default..."
if [[ "$WITH_UI" -eq 1 ]]; then
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile ui up -d --build
else
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
fi

# shellcheck disable=SC1090
set -a && source "$ENV_FILE" && set +a
HOST_PORT="${OCR_HOST_PORT:-8000}"

echo ""
echo "OCR backend is starting."
echo "  Host:              http://localhost:${HOST_PORT}"
echo "  Health:            http://localhost:${HOST_PORT}/api/health"
echo "  From translator:   http://ocr-backend:8000/api/ocr"
echo ""
echo "First OCR request downloads EasyOCR models (may take a few minutes)."
echo "Logs: docker compose -f $COMPOSE_FILE --env-file $ENV_FILE logs -f backend"
