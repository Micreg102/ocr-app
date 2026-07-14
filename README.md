# OCR App

A simple Docker-based OCR application with multiple engines. Upload an image or PDF through a React web UI and download the extracted text.

## Architecture

- **Backend** — FastAPI with pluggable OCR engines (`POST /api/ocr`)
- **Frontend** — React (Vite) with engine picker and drag-and-drop upload
- **Reverse proxy** — Nginx serves the frontend and proxies `/api` to the backend

## OCR engines

| Engine | Type | Best for |
|--------|------|----------|
| **PaddleOCR** | Deep learning | Complex layouts, multilingual text |
| **Tesseract** | Classic | Clean printed documents, speed |
| **EasyOCR** | Deep learning | Photos, varied fonts |

Models load on first use (lazy loading). The first request per engine downloads weights and may take a minute.

## Quick start

```bash
docker compose up --build
```

### Mac Studio (Apple Silicon)

See **[DEPLOY-MAC.md](DEPLOY-MAC.md)** for native and Docker deployment on Mac Studio.

```bash
git checkout mac
./scripts/mac/setup-native.sh    # native (recommended)
./scripts/mac/start-native.sh
# or
./scripts/deploy-docker-mac.sh   # Docker
```

| Service  | URL                        |
|----------|----------------------------|
| Web UI   | http://localhost:3000      |
| API      | http://localhost:8000      |
| Health   | http://localhost:8000/api/health |

## API

### `GET /api/engines`

Returns available OCR engines and the default.

### `POST /api/ocr`

Upload a file as `multipart/form-data`:

| Field | Required | Description |
|-------|----------|-------------|
| `file` | yes | Image or PDF |
| `engine` | no | `paddle`, `tesseract`, or `easyocr` (default: `paddle`) |

**Supported formats:** PNG, JPG, JPEG, BMP, TIFF, WebP, PDF

**Response:**

```json
{
  "filename": "document.pdf",
  "text": "--- Page 1 ---\nextracted text...",
  "line_count": 24,
  "block_count": 18,
  "page_count": 3,
  "pages": [
    {
      "page": 1,
      "width": 1654,
      "height": 2339,
      "blocks": [
        {
          "text": "Invoice",
          "confidence": 0.9821,
          "bbox": [[120.5, 80.0], [210.0, 80.0], [210.0, 105.5], [120.5, 105.5]],
          "box": { "x": 120.5, "y": 80.0, "width": 89.5, "height": 25.5 }
        }
      ]
    }
  ],
  "engine": "easyocr",
  "engine_name": "EasyOCR"
}
```

Each `block` contains:
- `text` — detected text fragment
- `confidence` — EasyOCR confidence score (0–1)
- `bbox` — four corner points `[[x,y], ...]` in image pixels
- `box` — axis-aligned bounding box `{x, y, width, height}`

### `GET /api/health`

Returns service status and list of available engine IDs.

## Frontend

1. Choose an OCR engine
2. Drop or click to select an image or PDF
3. Wait for processing
4. **Download result** (green) — saves a `.txt` file
5. **New file** (blue) — resets for another upload

## Configuration

| Variable        | Default | Description                         |
|-----------------|---------|-------------------------------------|
| `OCR_LANG`      | `en`    | Language code for all engines       |
| `OCR_DEFAULT_ENGINE` | `paddle` | Default engine (`paddle`, `tesseract`, `easyocr`) |
| `OCR_ENABLED_ENGINES` | all | Comma-separated engines to load |
| `OCR_USE_GPU`   | auto    | `1`/`0` — use GPU (Metal/CUDA) for EasyOCR |
| `PDF_RENDER_DPI`| `200`   | DPI for PDF-to-image conversion     |

Change in `docker-compose.yml` under the `backend` service.

Language support varies per engine. Tesseract ships with English and Polish packs in Docker. For other Tesseract languages, add `tesseract-ocr-<lang>` to the backend Dockerfile.

## Local development

**Backend:**

```bash
cd backend
pip install -r requirements.txt
# Tesseract binary required on host (apt/brew install tesseract)
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

## Project structure

```
ocr-app/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── engines/      # PaddleOCR, Tesseract, EasyOCR
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/App.jsx
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```
