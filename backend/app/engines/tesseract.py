import logging

import pytesseract
from PIL import Image

from .base import EngineInfo, OCRBlock, OCRPageResult, OCREngine
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

    def extract_page(self, image: Image.Image) -> OCRPageResult:
        rgb = image.convert("RGB")
        width, height = rgb.size
        lang = tesseract_lang()
        logger.info("Tesseract infer start (%sx%s, lang=%s)", width, height, lang)

        data = pytesseract.image_to_data(rgb, lang=lang, output_type=pytesseract.Output.DICT)
        blocks: list[OCRBlock] = []
        n = len(data.get("text", []))

        for i in range(n):
            text = (data["text"][i] or "").strip()
            if not text:
                continue
            try:
                conf = float(data["conf"][i])
            except (TypeError, ValueError):
                conf = -1.0
            if conf < 0:
                continue

            x = float(data["left"][i])
            y = float(data["top"][i])
            w = float(data["width"][i])
            h = float(data["height"][i])
            box = {
                "x": round(x, 2),
                "y": round(y, 2),
                "width": round(w, 2),
                "height": round(h, 2),
            }
            bbox = [
                [box["x"], box["y"]],
                [box["x"] + box["width"], box["y"]],
                [box["x"] + box["width"], box["y"] + box["height"]],
                [box["x"], box["y"] + box["height"]],
            ]
            blocks.append(
                OCRBlock(
                    text=text,
                    confidence=round(conf / 100.0, 4),
                    bbox=bbox,
                    box=box,
                )
            )

        logger.info("Tesseract infer done (%s blocks)", len(blocks))
        return OCRPageResult(width=width, height=height, blocks=blocks)

    def extract_text(self, image: Image.Image) -> str:
        return self.extract_page(image).text
