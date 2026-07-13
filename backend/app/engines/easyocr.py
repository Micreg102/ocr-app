import logging
import os

import easyocr
import numpy as np
from PIL import Image

from .base import EngineInfo, OCREngine
from .lang import easyocr_langs

logger = logging.getLogger(__name__)


def _use_gpu() -> bool:
    override = os.getenv("OCR_USE_GPU", "").strip().lower()
    if override in {"0", "false", "no"}:
        return False
    if override in {"1", "true", "yes"}:
        return True
    try:
        import torch

        return torch.cuda.is_available() or torch.backends.mps.is_available()
    except Exception:
        return False


class EasyOCREngine(OCREngine):
    info = EngineInfo(
        id="easyocr",
        name="EasyOCR",
        description="Deep learning OCR — good accuracy on varied fonts and photos",
    )

    def __init__(self) -> None:
        langs = easyocr_langs()
        use_gpu = _use_gpu()
        logger.info("Loading EasyOCR (langs=%s, gpu=%s)...", langs, use_gpu)
        self._reader = easyocr.Reader(langs, gpu=use_gpu, verbose=False)
        logger.info("EasyOCR ready")

    def extract_text(self, image: Image.Image) -> str:
        results = self._reader.readtext(np.array(image.convert("RGB")))
        return "\n".join(text for _, text, _ in results if text)
