import logging

import pytesseract
from PIL import Image

from .base import EngineInfo, OCREngine
from .lang import tesseract_lang

logger = logging.getLogger(__name__)


class TesseractEngine(OCREngine):
    info = EngineInfo(
        id="tesseract",
        name="Tesseract",
        description="Classic OCR — fast, best for clean printed documents",
    )

    def __init__(self) -> None:
        logger.info("Tesseract ready (lang=%s)", tesseract_lang())

    def extract_text(self, image: Image.Image) -> str:
        return pytesseract.image_to_string(image.convert("RGB"), lang=tesseract_lang()).strip()
