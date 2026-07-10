import logging

import easyocr
import numpy as np
from PIL import Image

from .base import EngineInfo, OCREngine
from .lang import easyocr_langs

logger = logging.getLogger(__name__)


class EasyOCREngine(OCREngine):
    info = EngineInfo(
        id="easyocr",
        name="EasyOCR",
        description="Deep learning OCR — good accuracy on varied fonts and photos",
    )

    def __init__(self) -> None:
        langs = easyocr_langs()
        logger.info("Loading EasyOCR (langs=%s)...", langs)
        self._reader = easyocr.Reader(langs, gpu=False, verbose=False)
        logger.info("EasyOCR ready")

    def extract_text(self, image: Image.Image) -> str:
        results = self._reader.readtext(np.array(image.convert("RGB")))
        return "\n".join(text for _, text, _ in results if text)
