import logging
import os

import easyocr
import numpy as np
from PIL import Image

from .base import EngineInfo, OCRBlock, OCRPageResult, OCREngine, bbox_to_box
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
        module_path = os.getenv("EASYOCR_MODULE_PATH", "").strip() or None
        logger.info(
            "Loading EasyOCR (langs=%s, gpu=%s, module_path=%s)...",
            langs,
            use_gpu,
            module_path or "~/.EasyOCR",
        )
        reader_kwargs = {"gpu": use_gpu, "verbose": False}
        if module_path:
            reader_kwargs["model_storage_directory"] = os.path.join(module_path, "model")
            reader_kwargs["user_network_directory"] = os.path.join(module_path, "user_network")
            os.makedirs(reader_kwargs["model_storage_directory"], exist_ok=True)
            os.makedirs(reader_kwargs["user_network_directory"], exist_ok=True)
        self._reader = easyocr.Reader(langs, **reader_kwargs)
        logger.info("EasyOCR ready")

    def extract_page(self, image: Image.Image) -> OCRPageResult:
        rgb = image.convert("RGB")
        width, height = rgb.size
        logger.info("EasyOCR infer start (%sx%s)", width, height)
        # workers=0 avoids multiprocessing issues inside Docker
        results = self._reader.readtext(np.array(rgb), workers=0)
        logger.info("EasyOCR infer done (%s blocks)", len(results) if results else 0)
        blocks: list[OCRBlock] = []

        for bbox, text, confidence in results:
            if not text:
                continue
            corners = [
                [round(float(point[0]), 2), round(float(point[1]), 2)]
                for point in bbox
            ]
            blocks.append(
                OCRBlock(
                    text=text,
                    confidence=round(float(confidence), 4),
                    bbox=corners,
                    box=bbox_to_box(bbox),
                )
            )

        return OCRPageResult(width=width, height=height, blocks=blocks)

    def extract_text(self, image: Image.Image) -> str:
        return self.extract_page(image).text
