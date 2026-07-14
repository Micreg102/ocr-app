from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from PIL import Image


@dataclass(frozen=True)
class EngineInfo:
    id: str
    name: str
    description: str


@dataclass(frozen=True)
class OCRBlock:
    text: str
    confidence: Optional[float]
    bbox: list[list[float]]
    box: dict[str, float]


@dataclass(frozen=True)
class OCRPageResult:
    width: int
    height: int
    blocks: list[OCRBlock]

    @property
    def text(self) -> str:
        return "\n".join(block.text for block in self.blocks if block.text)


def bbox_to_box(bbox: list) -> dict[str, float]:
    xs = [float(point[0]) for point in bbox]
    ys = [float(point[1]) for point in bbox]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    return {
        "x": round(x_min, 2),
        "y": round(y_min, 2),
        "width": round(x_max - x_min, 2),
        "height": round(y_max - y_min, 2),
    }


class OCREngine(ABC):
    info: EngineInfo

    def extract_page(self, image: Image.Image) -> OCRPageResult:
        text = self.extract_text(image)
        width, height = image.size
        blocks: list[OCRBlock] = []
        if text:
            blocks.append(
                OCRBlock(
                    text=text,
                    confidence=None,
                    bbox=[],
                    box={"x": 0.0, "y": 0.0, "width": float(width), "height": float(height)},
                )
            )
        return OCRPageResult(width=width, height=height, blocks=blocks)

    @abstractmethod
    def extract_text(self, image: Image.Image) -> str:
        pass
