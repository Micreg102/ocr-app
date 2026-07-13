#!/usr/bin/env bash
set -euo pipefail

pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite.*frontend" 2>/dev/null || true
echo "Stopped native OCR App processes."
