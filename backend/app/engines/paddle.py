import logging

import numpy as np
from paddleocr import PaddleOCR
from PIL import Image

from .base import EngineInfo, OCREngine
from .lang import OCR_LANG

logger = logging.getLogger(__name__)


class PaddleEngine(OCREngine):
    info = EngineInfo(
        id="paddle",
        name="PaddleOCR",
        description="Deep learning OCR — strong layout and multilingual support",
    )

    def __init__(self) -> None:
        logger.info("Loading PaddleOCR (lang=%s)...", OCR_LANG)
        self._ocr = PaddleOCR(use_angle_cls=True, lang=OCR_LANG, show_log=False)
        logger.info("PaddleOCR ready")

    def extract_text(self, image: Image.Image) -> str:
        result = self._ocr.ocr(np.array(image.convert("RGB")), cls=True)
        lines: list[str] = []
        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2:
                    text = line[1][0]
                    if text:
                        lines.append(text)
        return "\n".join(lines)
