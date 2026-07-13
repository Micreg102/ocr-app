# Deploy on Mac Studio (Apple Silicon)

This guide covers two deployment options on Mac Studio:

| Method | Best for | PaddleOCR | GPU (Metal) |
|--------|----------|-----------|-------------|
| **Native** (recommended) | Best performance, EasyOCR on Apple GPU | No | Yes (MPS) |
| **Docker** | Isolated, same as Linux deploy | Yes | No (CPU in container) |

## Prerequisites

- macOS on Apple Silicon (M1/M2/M3/M4)
- Mac Studio with at least 16 GB RAM (32+ GB recommended for EasyOCR)
- [Homebrew](https://brew.sh) (native deploy)
- [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) (Docker deploy)

## Option A — Native deploy (recommended)

Uses Homebrew Tesseract + EasyOCR with PyTorch MPS (Metal Performance Shaders) on the Mac Studio GPU.

### 1. Setup (one time)

```bash
git checkout mac
chmod +x scripts/mac/*.sh scripts/deploy-docker-mac.sh
./scripts/mac/setup-native.sh
```

This installs Tesseract, creates a Python venv, installs `requirements-mac.txt`, and copies `.env.mac.example` → `.env.mac`.

### 2. Configure

Edit `.env.mac`:

```bash
OCR_LANG=en
OCR_DEFAULT_ENGINE=easyocr
OCR_ENABLED_ENGINES=tesseract,easyocr
OCR_USE_GPU=1
```

| Variable | Description |
|----------|-------------|
| `OCR_LANG` | Language code (`en`, `pl`, …) |
| `OCR_DEFAULT_ENGINE` | Default engine in UI |
| `OCR_ENABLED_ENGINES` | Comma-separated list of active engines |
| `OCR_USE_GPU` | `1` = use Metal/CUDA if available, `0` = CPU only |

PaddleOCR is excluded from native Mac deploy — it has limited Apple Silicon support outside Docker.

### 3. Start

```bash
./scripts/mac/start-native.sh
```

| Service | URL |
|---------|-----|
| Web UI | http://localhost:3000 |
| API | http://localhost:8000 |
| Health | http://localhost:8000/api/health |

Stop with `Ctrl+C` or:

```bash
./scripts/mac/stop-native.sh
```

### 4. Run at login (optional)

1. Edit `deploy/com.ocr-app.plist` — replace `REPLACE_WITH_PROJECT_PATH` with the absolute project path (e.g. `/Users/you/projects/ocr-app`).
2. Create logs directory: `mkdir -p logs`
3. Install the service:

```bash
cp deploy/com.ocr-app.plist ~/Library/LaunchAgents/com.ocr-app.plist
launchctl load ~/Library/LaunchAgents/com.ocr-app.plist
```

Unload:

```bash
launchctl unload ~/Library/LaunchAgents/com.ocr-app.plist
```

## Option B — Docker deploy

Runs linux/arm64 containers via Docker Desktop. All three engines (Paddle, Tesseract, EasyOCR) are available.

### 1. Start

```bash
git checkout mac
chmod +x scripts/deploy-docker-mac.sh
./scripts/deploy-docker-mac.sh
```

Or manually:

```bash
docker compose -f docker-compose.yml -f docker-compose.mac.yml up --build -d
```

### 2. Configure (optional)

Create `.env.mac` or export variables before `docker compose`:

```bash
OCR_LANG=pl
OCR_DEFAULT_ENGINE=paddle
```

`docker-compose.mac.yml` sets `platform: linux/arm64` and allocates up to 8 GB RAM for the backend.

### 3. Logs and stop

```bash
docker compose -f docker-compose.yml -f docker-compose.mac.yml logs -f
docker compose -f docker-compose.yml -f docker-compose.mac.yml down
```

## Troubleshooting

**First OCR request is slow** — models download on first use (1–2 minutes per engine).

**Tesseract not found (native)** — run `brew install tesseract tesseract-lang`.

**EasyOCR GPU errors** — set `OCR_USE_GPU=0` in `.env.mac` to fall back to CPU.

**Docker build fails on ARM** — ensure Docker Desktop → Settings → General → “Use Virtualization framework” is enabled.

**Out of memory** — reduce enabled engines or increase Docker memory limit in Docker Desktop settings.

## Branch

All Mac-specific files live on the `mac` branch:

```
docker-compose.mac.yml
.env.mac.example
backend/requirements-mac.txt
scripts/deploy-docker-mac.sh
scripts/mac/setup-native.sh
scripts/mac/start-native.sh
scripts/mac/stop-native.sh
deploy/com.ocr-app.plist
DEPLOY-MAC.md
```
