# Deploy OCR App on Linux VM (owui01) — Docker CPU-only

Target: Linux VM with Docker, **no GPU**.  
Integrates with **local-ai-translator** via shared Docker network `alterai_default`.

| Item | Value |
|------|--------|
| Engine | EasyOCR (CPU) |
| Container | `ocr-backend` |
| Internal URL (translator) | `http://ocr-backend:8000` |
| Host URL (owui01) | `http://localhost:8000` (or `OCR_HOST_PORT`) |
| Network | `alterai_default` (external, must already exist) |

## Prerequisites

1. Docker + Docker Compose plugin on `owui01`
2. Network `alterai_default` already created by translator stack:

```bash
docker network ls | grep alterai_default
```

If missing, start local-ai-translator first (or create the network manually).

3. Enough RAM for EasyOCR on CPU — recommend **≥ 8 GB free** for the OCR container (default limit `6G`).

## Deploy

```bash
cd /path/to/ocr-app
git checkout mac   # or your deploy branch
chmod +x scripts/deploy-linux.sh

# optional: edit ports / language
cp .env.linux.example .env.linux
nano .env.linux

./scripts/deploy-linux.sh
```

With test UI (nginx frontend):

```bash
./scripts/deploy-linux.sh --ui
```

Manual equivalent:

```bash
docker compose -f docker-compose.linux.yml --env-file .env.linux up -d --build
```

## Verify

```bash
# From host
curl http://localhost:8000/api/health
# → {"status":"ok","engines":["easyocr"]}

# From another container on alterai_default (e.g. translator)
docker run --rm --network alterai_default curlimages/curl:8.5.0 \
  http://ocr-backend:8000/api/health

# OCR smoke test
curl -X POST http://localhost:8000/api/ocr -F "file=@sample.png"
```

## Configure local-ai-translator

Set OCR base URL to the **Docker service name** (not localhost):

```
OCR_API_URL=http://ocr-backend:8000
# or full endpoint:
OCR_API_URL=http://ocr-backend:8000/api/ocr
```

Translator must be on network `alterai_default` (same as this compose file).

### Example call from translator

```python
import requests

OCR_URL = "http://ocr-backend:8000/api/ocr"

with open("/path/to/document.pdf", "rb") as f:
    r = requests.post(OCR_URL, files={"file": f}, timeout=300)
r.raise_for_status()
data = r.json()

# data["text"] — full text
# data["pages"][*]["blocks"] — text + bbox/box for layout translation
```

Response shape: see [INTEGRATION-TRANSLATOR.md](INTEGRATION-TRANSLATOR.md).

## Useful commands

```bash
# Logs
docker compose -f docker-compose.linux.yml --env-file .env.linux logs -f backend

# Restart
docker compose -f docker-compose.linux.yml --env-file .env.linux restart backend

# Stop
docker compose -f docker-compose.linux.yml --env-file .env.linux down

# Rebuild after code change
docker compose -f docker-compose.linux.yml --env-file .env.linux up -d --build
```

## Notes

- **CPU only** — `OCR_USE_GPU=0` is forced; PyTorch installed from the CPU wheel index.
- **Models** — cached in volume `ocr-easyocr-models` (`/data/easyocr`). First OCR request is slow (download).
- **Port conflict** — change `OCR_HOST_PORT` in `.env.linux` (translator still uses `ocr-backend:8000` inside Docker).
- **Frontend** — optional (`--profile ui` / `--ui`). Translator does not need it.
- **Language** — set `OCR_LANG=pl` (or other) in `.env.linux` for Polish documents.

## Files

```
docker-compose.linux.yml
.env.linux.example
backend/Dockerfile.cpu
backend/requirements-docker.txt
scripts/deploy-linux.sh
DEPLOY-LINUX.md
```
