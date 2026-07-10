from .base import EngineInfo, OCREngine
from .easyocr import EasyOCREngine
from .paddle import PaddleEngine
from .tesseract import TesseractEngine

ENGINE_CLASSES: dict[str, type[OCREngine]] = {
    "paddle": PaddleEngine,
    "tesseract": TesseractEngine,
    "easyocr": EasyOCREngine,
}

ENGINE_CATALOG: list[EngineInfo] = [cls.info for cls in ENGINE_CLASSES.values()]

_instances: dict[str, OCREngine] = {}


def get_engine(engine_id: str) -> OCREngine:
    if engine_id not in ENGINE_CLASSES:
        raise ValueError(f"Unknown engine: {engine_id}")
    if engine_id not in _instances:
        _instances[engine_id] = ENGINE_CLASSES[engine_id]()
    return _instances[engine_id]
