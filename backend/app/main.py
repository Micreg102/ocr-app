import io
import logging
import os
import tempfile
from contextlib import asynccontextmanager

import fitz
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from paddleocr import PaddleOCR
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ocr_engine: PaddleOCR | None = None

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
PDF_EXTENSIONS = {".pdf"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS

PDF_RENDER_DPI = int(os.getenv("PDF_RENDER_DPI", "200"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ocr_engine
    lang = os.getenv("OCR_LANG", "en")
    logger.info("Loading PaddleOCR model (lang=%s)...", lang)
    ocr_engine = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
    logger.info("PaddleOCR ready")
    yield
    ocr_engine = None


app = FastAPI(title="OCR App API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_text(image_path: str) -> str:
    assert ocr_engine is not None
    result = ocr_engine.ocr(image_path, cls=True)
    lines: list[str] = []
    if result and result[0]:
        for line in result[0]:
            if line and len(line) >= 2:
                text = line[1][0]
                if text:
                    lines.append(text)
    return "\n".join(lines)


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


def ocr_image(image: Image.Image) -> str:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        image.convert("RGB").save(tmp.name)
        tmp_path = tmp.name
    try:
        return extract_text(tmp_path)
    finally:
        os.unlink(tmp_path)


def ocr_images(images: list[Image.Image]) -> str:
    parts: list[str] = []
    multi_page = len(images) > 1
    for i, image in enumerate(images):
        page_text = ocr_image(image)
        if multi_page:
            parts.append(f"--- Page {i + 1} ---")
        parts.append(page_text)
    return "\n\n".join(parts)


@app.get("/api/health")
async def health():
    return {"status": "ok", "ocr_loaded": ocr_engine is not None}


@app.post("/api/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
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

    try:
        if ext in PDF_EXTENSIONS:
            images = pdf_to_images(contents)
            if not images:
                raise HTTPException(status_code=400, detail="PDF contains no pages")
            text = ocr_images(images)
            page_count = len(images)
        else:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
            text = ocr_image(image)
            page_count = 1
    except HTTPException:
        raise
    except Exception as exc:
        if ext in PDF_EXTENSIONS:
            logger.exception("PDF processing failed")
            raise HTTPException(status_code=400, detail="Invalid or unreadable PDF file") from exc
        logger.exception("OCR processing failed")
        raise HTTPException(status_code=500, detail="OCR processing failed") from exc

    return {
        "filename": file.filename,
        "text": text,
        "line_count": len(text.splitlines()) if text else 0,
        "page_count": page_count,
    }
