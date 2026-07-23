# Deploy OCR App on Linux VM (owui01) — Docker CPU-only

Joins network **`alterai_default`** (local-ai-translator).

| Item | Value |
|------|--------|
| Engine | EasyOCR (CPU) |
| Container | `ocr-backend` |
| From translator | `http://ocr-backend:8000/api/ocr` |
| From host | `http://localhost:8100` |

## Prerequisites

```bash
docker network ls | grep alterai_default
```

Network must exist (start translator first).

## Start (normal Docker Compose)

```bash
git clone https://github.com/Micreg102/ocr-app.git
cd ocr-app
git checkout linux-deploy

cp .env.example .env   # optional
docker compose up -d --build
```

With test UI:

```bash
docker compose --profile ui up -d --build
```

## Verify

```bash
curl http://localhost:8100/api/health
# → {"status":"ok","engines":["easyocr"]}

docker run --rm --network alterai_default curlimages/curl:8.5.0 \
  http://ocr-backend:8000/api/health
```

## Translator config

```
OCR_API_URL=http://ocr-backend:8000
```

## Useful commands

```bash
docker compose logs -f backend
docker compose restart backend
docker compose down
docker compose up -d --build
```

## Notes

- First OCR request downloads EasyOCR models (slow once).
- Host port default is **8100**. Inside Docker, translator always uses `ocr-backend:8000`.
- Polish OCR: `OCR_LANG=pl` in `.env`.
- Frontend is optional (`--profile ui`).
