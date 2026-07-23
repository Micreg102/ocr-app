#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required."
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

if ! docker network inspect alterai_default >/dev/null 2>&1; then
  echo "ERROR: Docker network 'alterai_default' not found."
  echo "Start local-ai-translator first, then retry."
  exit 1
fi

PROFILE_ARGS=()
for arg in "$@"; do
  if [[ "$arg" == "--ui" ]]; then
    PROFILE_ARGS=(--profile ui)
  fi
done

echo "Starting OCR App (CPU-only)..."
docker compose "${PROFILE_ARGS[@]}" up -d --build

HOST_PORT=8000
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a && source .env && set +a
  HOST_PORT="${OCR_HOST_PORT:-8000}"
fi

echo ""
echo "  Host:            http://localhost:${HOST_PORT}"
echo "  Health:          http://localhost:${HOST_PORT}/api/health"
echo "  From translator: http://ocr-backend:8000/api/ocr"
echo ""
echo "Logs: docker compose logs -f backend"
