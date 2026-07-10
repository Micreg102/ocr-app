# OCR App

A simple Docker-based OCR application powered by [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR). Upload an image through a React web UI and download the extracted text.

## Architecture

- **Backend** — FastAPI + PaddleOCR (`POST /api/ocr`)
- **Frontend** — React (Vite) with drag-and-drop upload
- **Reverse proxy** — Nginx serves the frontend and proxies `/api` to the backend

## Quick start

```bash
docker compose up --build
```

First startup downloads PaddleOCR models (~100 MB) and can take a few minutes.

| Service  | URL                        |
|----------|----------------------------|
| Web UI   | http://localhost:3000      |
| API      | http://localhost:8000      |
| Health   | http://localhost:8000/api/health |

## API

### `POST /api/ocr`

Upload an image or PDF file as `multipart/form-data` with field `file`.

**Supported formats:** PNG, JPG, JPEG, BMP, TIFF, WebP, PDF

PDFs are converted to images internally (one page at a time) before OCR.

**Response:**

```json
{
  "filename": "document.pdf",
  "text": "--- Page 1 ---\nextracted text...",
  "line_count": 24,
  "page_count": 3
}
```

### `GET /api/health`

Returns service status and whether the OCR engine is loaded.

## Frontend

1. Drop or click to select an image or PDF
2. Wait for PaddleOCR to process
3. **Download result** (green) — saves a `.txt` file
4. **New file** (blue) — resets for another upload

## Configuration

| Variable        | Default | Description                         |
|-----------------|---------|-------------------------------------|
| `OCR_LANG`      | `en`    | PaddleOCR language code             |
| `PDF_RENDER_DPI`| `200`   | DPI for PDF-to-image conversion     |

Change in `docker-compose.yml` under the `backend` service. Common values: `en`, `ch`, `fr`, `german`, `korean`, `japan`.

## Local development

**Backend:**

```bash
cd backend
pip install -r requirements.txt
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
│   ├── app/main.py       # FastAPI + PaddleOCR
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/App.jsx       # Upload UI
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```
