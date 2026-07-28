# Deploy OCR App on Linux VM (owui01) — Docker CPU

Joins network **`alterai_default`** (local-ai-translator).

| Item | Value |
|------|--------|
| Engine | **Tesseract** (CPU — stable on small VMs) |
| Container | `ocr-backend` |
| From translator | `http://ocr-backend:8000/api/ocr` |
| From host | `http://localhost:8100` |

> EasyOCR/PyTorch was dropped for Linux Docker — it repeatedly crashed on this VM
> (NNPACK / inference kill). Mac native can still use EasyOCR.

## Start

```bash
git checkout linux-deploy
cp .env.example .env   # optional
docker compose up -d --build
```

If you already have `.env` with `easyocr`, change it to:

```bash
OCR_DEFAULT_ENGINE=tesseract
OCR_ENABLED_ENGINES=tesseract
```

## Verify

```bash
curl http://localhost:8100/api/health
# → {"status":"ok","engines":["tesseract"]}

curl -X POST http://localhost:8100/api/ocr \
  -F "file=@/tmp/test-ocr.png" \
  --max-time 60
```

## Translator

```
OCR_API_URL=http://ocr-backend:8000
```

Response still includes `pages[].blocks[]` with `text`, `box`, `bbox`, `confidence`.
