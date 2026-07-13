#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed. Install Docker Desktop for Mac first."
  exit 1
fi

if [[ -f .env.mac ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env.mac
  set +a
fi

echo "Building and starting OCR App (Apple Silicon / linux/arm64)..."
docker compose -f docker-compose.yml -f docker-compose.mac.yml up --build -d

echo ""
echo "OCR App is starting."
echo "  Web UI:  http://localhost:3000"
echo "  API:     http://localhost:8000"
echo "  Health:  http://localhost:8000/api/health"
echo ""
echo "First OCR request per engine may take 1–2 minutes (model download)."
echo "Logs: docker compose -f docker-compose.yml -f docker-compose.mac.yml logs -f"
