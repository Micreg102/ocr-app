import os

OCR_LANG = os.getenv("OCR_LANG", "en")

TESSERACT_LANG_MAP = {
    "en": "eng",
    "pl": "pol",
    "de": "deu",
    "fr": "fra",
    "es": "spa",
    "it": "ita",
    "pt": "por",
    "ru": "rus",
    "ja": "jpn",
    "ko": "kor",
    "ch": "chi_sim",
    "zh": "chi_sim",
}


def tesseract_lang() -> str:
    return TESSERACT_LANG_MAP.get(OCR_LANG, OCR_LANG)


def easyocr_langs() -> list[str]:
    # EasyOCR uses ISO 639-1 codes; fall back to English + detected lang.
    lang = OCR_LANG if OCR_LANG not in ("ch", "zh") else "ch_sim"
    if lang == "en":
        return ["en"]
    return [lang, "en"]
