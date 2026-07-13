import os

from .base import EngineInfo, OCREngine

_ENGINE_LOADERS: dict[str, tuple[str, str]] = {
    "paddle": (".paddle", "PaddleEngine"),
    "tesseract": (".tesseract", "TesseractEngine"),
    "easyocr": (".easyocr", "EasyOCREngine"),
}


def _enabled_engine_ids() -> set[str]:
    raw = os.getenv("OCR_ENABLED_ENGINES", "").strip()
    if not raw:
        return set(_ENGINE_LOADERS)
    return {engine_id for engine_id in raw.split(",") if engine_id.strip() in _ENGINE_LOADERS}


def _load_engine_class(engine_id: str) -> type[OCREngine]:
    module_name, class_name = _ENGINE_LOADERS[engine_id]
    import importlib

    module = importlib.import_module(module_name, package=__package__)
    return getattr(module, class_name)


def _build_engine_classes() -> dict[str, type[OCREngine]]:
    enabled = _enabled_engine_ids()
    return {engine_id: _load_engine_class(engine_id) for engine_id in enabled}


ENGINE_CLASSES: dict[str, type[OCREngine]] = _build_engine_classes()
ENGINE_CATALOG: list[EngineInfo] = [cls.info for cls in ENGINE_CLASSES.values()]

_instances: dict[str, OCREngine] = {}


def get_engine(engine_id: str) -> OCREngine:
    if engine_id not in ENGINE_CLASSES:
        raise ValueError(f"Unknown engine: {engine_id}")
    if engine_id not in _instances:
        _instances[engine_id] = ENGINE_CLASSES[engine_id]()
    return _instances[engine_id]
