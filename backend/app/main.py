import asyncio
import io
import logging
import os

import fitz
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

from app.engines import ENGINE_CATALOG, get_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
PDF_EXTENSIONS = {".pdf"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS
DEFAULT_ENGINE = os.getenv("OCR_DEFAULT_ENGINE", "paddle")

PDF_RENDER_DPI = int(os.getenv("PDF_RENDER_DPI", "200"))


def resolved_default_engine() -> str:
    enabled = {e.id for e in ENGINE_CATALOG}
    if DEFAULT_ENGINE in enabled:
        return DEFAULT_ENGINE
    if enabled:
        return next(iter(enabled))
    return DEFAULT_ENGINE

app = FastAPI(title="OCR App API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def pdf_to_images(pdf_bytes: bytes, dpi: int = PDF_RENDER_DPI) -> list[Image.Image]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images: list[Image.Image] = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    try:
        for page in doc:
            pix = page.get_pixmap(matrix=matrix)
            images.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
    finally:
        doc.close()
    return images


def block_to_dict(block) -> dict:
    return {
        "text": block.text,
        "confidence": block.confidence,
        "bbox": block.bbox,
        "box": block.box,
    }


def run_ocr_pages(images: list[Image.Image], engine_id: str) -> list[dict]:
    engine = get_engine(engine_id)
    pages: list[dict] = []
    for index, image in enumerate(images):
        page_result = engine.extract_page(image)
        pages.append(
            {
                "page": index + 1,
                "width": page_result.width,
                "height": page_result.height,
                "blocks": [block_to_dict(block) for block in page_result.blocks],
            }
        )
    return pages


def process_upload(contents: bytes, ext: str, engine_id: str) -> tuple[list[dict], int]:
    """CPU-heavy OCR work — runs in a worker thread so /api/health stays responsive."""
    if ext in PDF_EXTENSIONS:
        images = pdf_to_images(contents)
        if not images:
            raise ValueError("PDF contains no pages")
        pages = run_ocr_pages(images, engine_id)
        return pages, len(images)

    image = Image.open(io.BytesIO(contents)).convert("RGB")
    pages = run_ocr_pages([image], engine_id)
    return pages, 1


def pages_to_text(pages: list[dict]) -> str:
    parts: list[str] = []
    multi_page = len(pages) > 1
    for page in pages:
        page_text = "\n".join(block["text"] for block in page["blocks"] if block["text"])
        if multi_page:
            parts.append(f"--- Page {page['page']} ---")
        parts.append(page_text)
    return "\n\n".join(parts)


@app.get("/api/health")
async def health():
    return {"status": "ok", "engines": [e.id for e in ENGINE_CATALOG]}


@app.get("/api/engines")
async def list_engines():
    return {
        "engines": [
            {"id": e.id, "name": e.name, "description": e.description}
            for e in ENGINE_CATALOG
        ],
        "default": resolved_default_engine(),
    }


@app.post("/api/ocr")
async def ocr_endpoint(
    file: UploadFile = File(...),
    engine: str = Form(default=""),
):
    if not ENGINE_CATALOG:
        raise HTTPException(status_code=503, detail="No OCR engines are enabled")

    selected_engine = engine or resolved_default_engine()

    if selected_engine not in {e.id for e in ENGINE_CATALOG}:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown engine '{selected_engine}'. Available: {', '.join(e.id for e in ENGINE_CATALOG)}",
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    engine_info = next(e for e in ENGINE_CATALOG if e.id == selected_engine)

    try:
        pages, page_count = await asyncio.to_thread(
            process_upload, contents, ext, selected_engine
        )
        text = pages_to_text(pages)
        block_count = sum(len(page["blocks"]) for page in pages)
    except HTTPException:
        raise
    except UnidentifiedImageError as exc:
        logger.warning("Unreadable image upload: %s", file.filename)
        raise HTTPException(
            status_code=400,
            detail="Invalid or unreadable image file. Use a real PNG/JPG/PDF.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        if ext in PDF_EXTENSIONS:
            logger.exception("PDF processing failed")
            raise HTTPException(status_code=400, detail="Invalid or unreadable PDF file") from exc
        logger.exception("OCR processing failed (engine=%s)", selected_engine)
        raise HTTPException(status_code=500, detail="OCR processing failed") from exc

    return {
        "filename": file.filename,
        "text": text,
        "line_count": len(text.splitlines()) if text else 0,
        "block_count": block_count,
        "page_count": page_count,
        "pages": pages,
        "engine": selected_engine,
        "engine_name": engine_info.name,
    }
