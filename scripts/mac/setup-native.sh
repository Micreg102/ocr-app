#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "=== OCR App — Mac Studio native setup ==="

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install from https://brew.sh"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install with: brew install python@3.11"
  exit 1
fi

PYTHON_BIN="$(command -v python3.11 || command -v python3.12 || command -v python3)"
PYTHON_VERSION="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "Using Python $PYTHON_VERSION ($PYTHON_BIN)"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required. Install with: brew install node"
  exit 1
fi

echo "Creating Python virtual environment..."
"$PYTHON_BIN" -m venv backend/.venv
# shellcheck disable=SC1091
source backend/.venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements-mac.txt

echo "Installing frontend dependencies..."
(cd frontend && npm install)

if [[ ! -f .env.mac ]]; then
  cp .env.mac.example .env.mac
  echo "Created .env.mac from example — review before starting."
fi

echo ""
echo "Setup complete. Start the app with:"
echo "  ./scripts/mac/start-native.sh"
