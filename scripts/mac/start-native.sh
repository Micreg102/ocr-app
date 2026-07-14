#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ ! -d backend/.venv ]]; then
  echo "Virtual environment not found. Run ./scripts/mac/setup-native.sh first."
  exit 1
fi

if [[ -f .env.mac ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env.mac
  set +a
fi

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
export OCR_LANG="${OCR_LANG:-en}"
export OCR_DEFAULT_ENGINE="${OCR_DEFAULT_ENGINE:-easyocr}"
export OCR_ENABLED_ENGINES="${OCR_ENABLED_ENGINES:-easyocr}"
export OCR_USE_GPU="${OCR_USE_GPU:-1}"
export PDF_RENDER_DPI="${PDF_RENDER_DPI:-200}"

# shellcheck disable=SC1091
source backend/.venv/bin/activate

cleanup() {
  echo ""
  echo "Stopping OCR App..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting backend on port $BACKEND_PORT..."
(cd backend && uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT") &
BACKEND_PID=$!

echo "Starting frontend on port $FRONTEND_PORT (proxy → $BACKEND_PORT)..."
(cd frontend && VITE_PROXY_TARGET="http://localhost:${BACKEND_PORT}" npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT") &
FRONTEND_PID=$!

echo ""
echo "OCR App running (native Mac Studio):"
echo "  Web UI:  http://localhost:${FRONTEND_PORT}"
echo "  API:     http://localhost:${BACKEND_PORT}"
echo "  Engines: ${OCR_ENABLED_ENGINES}"
echo "  Default: ${OCR_DEFAULT_ENGINE}"
echo ""
echo "Press Ctrl+C to stop."

wait
